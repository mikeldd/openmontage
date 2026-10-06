#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.checkpoint import init_project, write_checkpoint
from tools.audio.piper_tts import PiperTTS
from tools.audio.pixabay_music import PixabayMusic
from tools.subtitle.subtitle_gen import SubtitleGen
from tools.video.stock_sources.base import SearchFilters
from tools.video.stock_sources.wikimedia import WikimediaSource

PROJECT_ID = "healthcare-autopsy-theranos-e01"
PACKAGE_PATH = ROOT / "production" / "theranos-episode-1" / "approved_package.json"

def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)
    ], text=True).strip()
    return float(out)

def atempo_chain(factor: float) -> str:
    parts=[]
    f=factor
    while f > 2.0:
        parts.append("atempo=2.0")
        f /= 2.0
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    parts.append(f"atempo={f:.6f}")
    return ",".join(parts)

def normalize_narration(raw: Path, final: Path, target: float) -> float:
    dur = probe_duration(raw)
    final.parent.mkdir(parents=True, exist_ok=True)
    if dur > target:
        factor = dur / target
        af = atempo_chain(factor)
        subprocess.run([
            "ffmpeg","-y","-i",str(raw),"-af",af,"-t",f"{target:.3f}",
            "-ar","48000","-ac","2","-c:a","pcm_s16le",str(final)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run([
            "ffmpeg","-y","-i",str(raw),
            "-af",f"apad=pad_dur={max(0.0,target-dur):.3f}",
            "-t",f"{target:.3f}","-ar","48000","-ac","2","-c:a","pcm_s16le",str(final)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return probe_duration(final)

def sentence_cues(text: str, start: float, end: float):
    sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+|\n\n+', text.strip()) if s.strip()]
    if not sentences:
        return []
    total_words=sum(max(1,len(s.split())) for s in sentences)
    available=max(0.5,end-start)
    t=start
    out=[]
    for i,s in enumerate(sentences):
        frac=max(1,len(s.split()))/total_words
        d=available*frac
        seg_end=end if i==len(sentences)-1 else min(end,t+d)
        out.append({"text":s,"start":t,"end":seg_end})
        t=seg_end
    return out

def find_wikimedia_clip(source, queries, used_ids):
    filters=SearchFilters(kind="video",per_page=25,min_duration=3,orientation="landscape",min_width=640)
    for query in queries:
        hits=source.search(query,filters)
        for cand in hits:
            if cand.kind!="video" or not cand.download_url:
                continue
            if cand.clip_id in used_ids:
                continue
            if cand.width and cand.height and cand.width < cand.height:
                continue
            used_ids.add(cand.clip_id)
            return query,cand
    return None,None

def download_preview(source, cand, output: Path, seconds: int=12):
    raw=output.with_name(output.stem+"_raw"+output.suffix)
    source.download(cand,raw)
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([
        "ffmpeg","-y","-i",str(raw),"-t",str(seconds),
        "-vf","scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:v","libx264","-preset","veryfast","-crf","22","-an",str(output)
    ],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    raw.unlink(missing_ok=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--piper-dir",required=True)
    args=ap.parse_args()

    pkg=json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    project=init_project(PROJECT_ID,title=pkg["title"],pipeline_type="hybrid")
    artifacts=project/"artifacts"
    for name in ("brief","script","scene_plan"):
        dump(artifacts/f"{name}.json",pkg[name])

    write_checkpoint(ROOT/"projects",PROJECT_ID,"idea","completed",{"brief":pkg["brief"]},
        pipeline_type="hybrid",human_approval_required=True,human_approved=True)
    write_checkpoint(ROOT/"projects",PROJECT_ID,"script","completed",{"script":pkg["script"]},
        pipeline_type="hybrid",human_approval_required=True,human_approved=True)
    write_checkpoint(ROOT/"projects",PROJECT_ID,"scene_plan","completed",{"scene_plan":pkg["scene_plan"]},
        pipeline_type="hybrid",human_approval_required=True,human_approved=True)

    model=list(Path(args.piper_dir).glob("en_US-lessac-medium.onnx"))
    if not model:
        raise RuntimeError("Piper voice model missing")

    manifest_assets=[]
    concat_lines=[]
    subtitle_segments=[]

    for sec in pkg["script"]["sections"]:
        sec_id=sec["id"]
        raw=project/"assets"/"audio"/f"{sec_id}_raw.wav"
        final=project/"assets"/"audio"/f"{sec_id}.wav"
        result=PiperTTS().execute({
            "text":sec["text"],"model":str(model[0]),"speaker_id":0,
            "length_scale":1.03,"sentence_silence":0.28,"output_path":str(raw)
        })
        if not result.success:
            raise RuntimeError(result.error)
        target=float(sec["end_seconds"]-sec["start_seconds"])
        normalized=normalize_narration(raw,final,target)
        raw.unlink(missing_ok=True)
        concat_lines.append(f"file '{final.resolve()}'")
        subtitle_segments.extend(sentence_cues(sec["text"],float(sec["start_seconds"]),float(sec["end_seconds"])))
        manifest_assets.append({
            "id":f"narration-{sec_id}","type":"narration",
            "path":f"assets/audio/{sec_id}.wav","source_tool":"piper_tts",
            "scene_id":sec_id,"model":"en_US-lessac-medium","cost_usd":0,
            "duration_seconds":round(normalized,3),"format":"wav",
            "subtype":"final_narration_segment",
            "generation_summary":"Approved OpenMontage Piper narration, normalized to the locked scene duration.",
            "provider":"piper",
            "voice_performance":{
                "source_section_id":sec_id,"delivery_cues_applied":True,
                "provider_text_used":True,
                "provider_settings":{"length_scale":1.03,"sentence_silence":0.28},
                "sample_approved":True,
                "sample_path":"assets/audio/sample_hook_piper.wav" if sec_id=="hook" else "",
                "review_notes":"Assets direction approved by user on 2026-10-06."
            }
        })

    concat_file=project/"assets"/"audio"/"concat.txt"
    concat_file.write_text("\n".join(concat_lines),encoding="utf-8")
    full_narr=project/"assets"/"audio"/"narration_full.wav"
    subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0","-i",str(concat_file),
        "-c","copy",str(full_narr)
    ],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    manifest_assets.append({
        "id":"narration-full","type":"narration","path":"assets/audio/narration_full.wav",
        "source_tool":"ffmpeg_concat","scene_id":"s01-s19","cost_usd":0,
        "duration_seconds":round(probe_duration(full_narr),3),"format":"wav",
        "subtype":"final_narration_master",
        "generation_summary":"Concatenated normalized Piper narration master.","provider":"openmontage"
    })

    sub_out=project/"assets"/"subtitles.srt"
    sub=SubtitleGen().execute({
        "segments":subtitle_segments,"format":"srt","output_path":str(sub_out),
        "max_words_per_cue":8,"max_chars_per_line":42,"highlight_style":"none"
    })
    if not sub.success:
        raise RuntimeError(sub.error)
    manifest_assets.append({
        "id":"subtitles","type":"subtitle","path":"assets/subtitles.srt",
        "source_tool":"subtitle_gen","scene_id":"s01-s19","cost_usd":0,
        "format":"srt","subtype":"burned_caption_source",
        "generation_summary":"OpenMontage sentence-timed captions from locked section timings.",
        "provider":"openmontage"
    })

    source=WikimediaSource()
    used=set()
    broll_specs=[
        ("broll-blood-collection","s01",["blood test finger prick","capillary blood sampling","blood collection"]),
        ("broll-lab-analyzer","s02",["clinical laboratory analyzer","medical laboratory equipment","laboratory analyzer"]),
        ("broll-silicon-valley","s04",["Silicon Valley California","Palo Alto California","California technology campus"]),
        ("broll-venipuncture","s05",["venipuncture blood draw","blood collection medical","phlebotomy"]),
        ("broll-pharmacy","s06",["pharmacy interior","pharmacy store","drugstore pharmacy"]),
        ("broll-lab-tech","s08",["medical laboratory technician","clinical laboratory","laboratory scientist"]),
        ("broll-quiet-lab","s16",["laboratory interior","medical laboratory","laboratory equipment"]),
        ("broll-clinician-review","s17",["doctor computer hospital","clinician medical records","hospital doctor computer"])
    ]
    provenance=[]
    for asset_id,scene_id,queries in broll_specs:
        q,cand=find_wikimedia_clip(source,queries,used)
        if cand is None:
            provenance.append({"asset_id":asset_id,"status":"not_found","queries":queries})
            continue
        out=project/"assets"/"video"/f"{asset_id}.mp4"
        download_preview(source,cand,out,12)
        rec={
            "asset_id":asset_id,"provider":"wikimedia","query":q,
            "source_id":cand.source_id,"source_url":cand.source_url,
            "download_url":cand.download_url,"creator":cand.creator,
            "license":cand.license,"source_tags":cand.source_tags,
            "source_width":cand.width,"source_height":cand.height,
            "source_duration":cand.duration
        }
        provenance.append(rec)
        manifest_assets.append({
            "id":asset_id,"type":"video","path":f"assets/video/{asset_id}.mp4",
            "source_tool":"wikimedia_stock_source","scene_id":scene_id,"cost_usd":0,
            "duration_seconds":12,"resolution":"1280x720","format":"mp4",
            "subtype":"documentary_stock",
            "generation_summary":"Real motion footage sourced through the OpenMontage Wikimedia Commons adapter.",
            "provider":"wikimedia","license":cand.license,"original_url":cand.source_url
        })
    dump(artifacts/"broll_provenance.json",provenance)

    music_path=project/"assets"/"music"/"documentary_underscore.mp3"
    music_result=None
    music_queries=[
        "minimal documentary ambient technology",
        "serious documentary ambient",
        "subtle corporate documentary"
    ]
    music_tool=PixabayMusic()
    for q in music_queries:
        r=music_tool.execute({"query":q,"min_duration":60,"max_duration":600,"output_path":str(music_path)})
        if r.success:
            music_result=r
            break
    if music_result and music_path.exists():
        md=music_result.data
        manifest_assets.append({
            "id":"music-underscore","type":"music","path":"assets/music/documentary_underscore.mp3",
            "source_tool":"pixabay_music","scene_id":"s01-s19","cost_usd":0,
            "duration_seconds":float(md.get("duration_seconds") or probe_duration(music_path)),
            "format":"mp3","subtype":"documentary_underscore",
            "generation_summary":"Understated documentary underscore sourced through OpenMontage Pixabay Music.",
            "provider":"pixabay_music",
            "license":md.get("license","Pixabay Content License")
        })

    animation_dir=project/"assets"/"animation"
    animation_dir.mkdir(parents=True,exist_ok=True)
    motion_specs={
      "style":{"palette":{"navy":"#1E293B","red":"#DC2626","blue":"#0EA5E9","white":"#FFFFFF","gray":"#94A3B8"},"tone":"premium restrained healthcare investigative","red_usage":"warnings and failures only"},
      "scenes":{
        "s03":{"device":"title evidence reveal","title":"Theranos: When the Blood Test Didn’t Work"},
        "s07":{"device":"lab workflow","steps":["Patient","Blood sample","Analyzer","VALIDATION","Result","Clinician decision"],"validation_line":"Accuracy and reproducibility are not optional."},
        "s09":{"device":"validation checklist","items":["Specimen type","Accuracy","Precision","Quality control","Reportable range","Reference interval"]},
        "s10":{"device":"capillary vs venous comparison","question":"Was the technology validated well enough for clinicians to make decisions from the results?"},
        "s11":{"device":"timeline","dates":["2003","2013","2015–16","2018","2022"]},
        "s12":{"device":"regulatory evidence card","label":"CMS / HHS","quote":"practices and procedures ... presented immediate jeopardy to patient health","guardrail":"Regulatory finding, not a criminal verdict."},
        "s13":{"device":"civil/commercial chronology","labels":["Walgreens — relationship terminated, June 2016","SEC — civil securities fraud allegations, March 2018"]},
        "s14":{"device":"separate verdict cards","holmes":"Jury convicted on 4 investor-fraud-related counts; 135 months.","balwani":"Separate jury convicted on all 12 counts in his case; 155 months."},
        "s15":{"device":"three-column distinction","columns":["BUSINESS FAILURE","REGULATORY & COMPLIANCE FAILURE","CRIMINAL CONVICTIONS"]},
        "s18":{"device":"host placeholder","text":"HOST FOOTAGE REQUIRED — DR. MIKE DANIELS","subtext":"Final host shot pending."},
        "s19":{"device":"works cited","sources":["U.S. Department of Justice","U.S. Securities and Exchange Commission","Centers for Medicare & Medicaid Services / HHS","Federal court records and sentencing materials","Walgreens corporate releases","WHO specimen-collection guidance"],"disclaimer":"This episode is educational commentary based on public records and cited sources.","brand":"ThePodiatryVoice.com"}
      }
    }
    motion_path=animation_dir/"motion_specs.json"
    dump(motion_path,motion_specs)
    manifest_assets.append({
        "id":"motion-specs","type":"animation","path":"assets/animation/motion_specs.json",
        "source_tool":"openmontage_bespoke_spec","scene_id":"s03-s19","cost_usd":0,
        "format":"json","subtype":"atelier_motion_spec",
        "generation_summary":"Locked bespoke motion-graphics specification for the approved documentary scenes.",
        "provider":"openmontage"
    })

    evidence={
      "DOJ Holmes verdict":"https://www.justice.gov/usao-ndca/pr/theranos-founder-elizabeth-holmes-found-guilty-investor-fraud",
      "DOJ Balwani verdict":"https://www.justice.gov/usao-ndca/pr/theranos-chief-operating-officer-ramesh-sunny-balwani-found-guilty-conspiracy-wire",
      "DOJ Balwani sentence":"https://www.justice.gov/usao-ndca/pr/theranos-president-sentenced-more-12-years-fraud-jeopardized-patient-health-and-bilked",
      "SEC civil release":"https://www.sec.gov/enforcement-litigation/litigation-releases/lr-24069",
      "HHS ALJ decision":"https://www.hhs.gov/about/agencies/dab/decisions/alj-decisions/2025/alj-cr6674/index.html",
      "Walgreens termination":"https://www.walgreensbootsalliance.com/news-media/press-releases/2016/walgreens-terminates-relationship-with-theranos-will-be-closing-operations-at-all-40-theranos-wellness-centers-in-arizona"
    }
    evidence_path=project/"assets"/"evidence_sources.json"
    dump(evidence_path,evidence)
    manifest_assets.append({
        "id":"evidence-sources","type":"code_snippet","path":"assets/evidence_sources.json",
        "source_tool":"openmontage_research_lock","scene_id":"s06-s19","cost_usd":0,
        "format":"json","subtype":"source_map",
        "generation_summary":"Primary-source URL map carried into edit and compose for precise on-screen attribution.",
        "provider":"openmontage"
    })

    manifest={
      "version":"1.0","assets":manifest_assets,"total_cost_usd":0,
      "metadata":{
        "stage":"assets","status":"completed","sample_preview_approved":True,
        "full_batch_generated":True,
        "broll_provider":"wikimedia","voice_provider":"piper",
        "music_provider":"pixabay_music" if music_result else "unresolved",
        "caption_timing":"sentence-level because Piper does not provide word timestamps"
      }
    }
    dump(artifacts/"asset_manifest.json",manifest)

    decisions={
      "version":"1.0","project_id":PROJECT_ID,"decisions":[
        {
          "decision_id":"d-assets-001","stage":"assets","category":"voice_selection",
          "subject":"Narration TTS provider",
          "options_considered":[
            {"option_id":"piper","label":"Piper local TTS","score":0.82,"reason":"OpenMontage-native, zero-cost, deterministic and approved by the user for this asset direction."},
            {"option_id":"cloud-premium","label":"Premium cloud TTS","score":0.88,"reason":"Potentially more natural but would introduce a new provider and possible cost.","rejected_because":"No provider substitution is necessary after assets approval."}
          ],
          "selected":"piper","reason":"Preserve the approved OpenMontage-only, zero-cost narration path.",
          "user_visible":True,"user_approved":True,"confidence":0.97
        },
        {
          "decision_id":"d-assets-003","stage":"assets","category":"provider_selection",
          "subject":"Documentary B-roll source",
          "options_considered":[
            {"option_id":"wikimedia","label":"Wikimedia Commons","score":0.91,"reason":"No API key, per-file provenance and licensing, strong fit for evidence-led documentary."},
            {"option_id":"coverr","label":"Coverr","score":0.25,"reason":"Good stock fit but unavailable in execution.","rejected_because":"HTTP 401 Unauthorized."}
          ],
          "selected":"wikimedia","reason":"User explicitly approved Wikimedia after the Coverr blocker.",
          "user_visible":True,"user_approved":True,"confidence":0.99
        },
        {
          "decision_id":"d-assets-004","stage":"assets","category":"music_source",
          "subject":"Documentary underscore source",
          "options_considered":[
            {"option_id":"pixabay_music","label":"Pixabay Music via OpenMontage","score":0.86,"reason":"Zero-cost, commercial-use stock music integrated into OpenMontage."},
            {"option_id":"no_music","label":"No underscore","score":0.40,"reason":"Would reduce risk but violate the approved sound direction.","rejected_because":"Approved brief calls for understated documentary music."}
          ],
          "selected":"pixabay_music" if music_result else "no_music",
          "reason":"Use the OpenMontage zero-cost music path when available; do not introduce a paid provider.",
          "user_visible":True,"user_approved":False,"confidence":0.86
        }
      ]
    }
    dump(artifacts/"decision_log_assets.json",decisions)

    write_checkpoint(ROOT/"projects",PROJECT_ID,"assets","completed",
        {"asset_manifest":manifest,"decision_log":decisions},
        pipeline_type="hybrid",human_approval_required=True,human_approved=True,
        cost_snapshot={"total_spent_usd":0.0,"total_reserved_usd":0.0,"budget_remaining_usd":2.0},
        metadata={"gate":"assets","approved_by_user":True,"full_batch_generated":True})

    print(json.dumps({
        "status":"assets_completed","project":str(project),
        "asset_count":len(manifest_assets),
        "broll_count":len([a for a in manifest_assets if a["type"]=="video"]),
        "music_present":bool(music_result),
        "narration_duration":probe_duration(full_narr)
    },indent=2))

if __name__=="__main__":
    main()
