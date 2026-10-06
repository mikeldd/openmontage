
import React from "react";
import {
  AbsoluteFill, Audio, Composition, Sequence, Video, interpolate,
  registerRoot, staticFile, useCurrentFrame, useVideoConfig
} from "remotion";

type Caption={start:number;end:number;lines:string[]};
type Props={captions:Caption[];musicPresent:boolean};

const C={navy:"#0F172A",navy2:"#1E293B",blue:"#0EA5E9",red:"#DC2626",white:"#F8FAFC",gray:"#94A3B8",line:"#334155"};
const FPS=30;
const sec=(s:number)=>Math.round(s*FPS);
const fade=(f:number,d=14)=>interpolate(f,[0,d],[0,1],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});

const Brand=()=>(
  <div style={{position:"absolute",top:42,right:54,fontFamily:"Arial,Helvetica,sans-serif",fontSize:24,fontWeight:800,letterSpacing:1.3,color:C.white,opacity:.88,zIndex:60}}>
    HEALTHCARE <span style={{color:C.blue}}>AUTOPSY</span>
    <div style={{fontSize:13,fontWeight:500,letterSpacing:.8,color:C.gray,textAlign:"right",marginTop:5}}>ThePodiatryVoice.com</div>
  </div>
);

const Grain=()=>(
  <AbsoluteFill style={{pointerEvents:"none",opacity:.055,backgroundImage:"radial-gradient(rgba(255,255,255,.55) .6px, transparent .7px)",backgroundSize:"4px 4px",mixBlendMode:"soft-light"}}/>
);

const VideoBed=({src,label}:{src:string;label?:string})=>{
  const f=useCurrentFrame();
  const cfg=useVideoConfig();
  const scale=1.02+interpolate(f,[0,cfg.durationInFrames],[0,.035],{extrapolateRight:"clamp"});
  return <AbsoluteFill style={{background:C.navy,overflow:"hidden"}}>
    <Video src={staticFile(src)} loop muted style={{width:"100%",height:"100%",objectFit:"cover",transform:"scale("+scale+")"}}/>
    <AbsoluteFill style={{background:"linear-gradient(90deg,rgba(15,23,42,.88),rgba(15,23,42,.40) 56%,rgba(15,23,42,.24))"}}/>
    <AbsoluteFill style={{background:"linear-gradient(180deg,rgba(15,23,42,.08),rgba(15,23,42,.60))"}}/>
    {label?<div style={{position:"absolute",left:58,bottom:50,fontFamily:"Arial,Helvetica,sans-serif",fontSize:14,letterSpacing:.8,color:"rgba(248,250,252,.54)"}}>{label}</div>:null}
    <Grain/><Brand/>
  </AbsoluteFill>;
};

const BigText=({eyebrow,title,body,red=false}:{eyebrow?:string;title:string;body?:string;red?:boolean})=>{
  const f=useCurrentFrame();
  return <div style={{position:"absolute",left:102,top:188,width:1150,opacity:fade(f),fontFamily:"Arial,Helvetica,sans-serif",zIndex:20}}>
    {eyebrow?<div style={{fontSize:21,fontWeight:900,letterSpacing:2.2,color:red?C.red:C.blue,marginBottom:22}}>{eyebrow.toUpperCase()}</div>:null}
    <div style={{fontFamily:"Georgia,Times New Roman,serif",fontSize:76,lineHeight:1.04,fontWeight:700,color:C.white,letterSpacing:-1.6}}>{title}</div>
    {body?<div style={{fontSize:30,lineHeight:1.4,color:"#CBD5E1",marginTop:28,maxWidth:1010}}>{body}</div>:null}
  </div>;
};

const SourceChip=({children}:{children:React.ReactNode})=>(
  <div style={{display:"inline-flex",alignItems:"center",gap:10,padding:"8px 13px",border:"1px solid "+C.line,background:"rgba(15,23,42,.80)",borderRadius:6,fontFamily:"Arial,Helvetica,sans-serif",fontSize:18,color:C.gray,letterSpacing:.6}}>
    <span style={{width:7,height:7,borderRadius:99,background:C.blue}}/>SOURCE: {children}
  </div>
);

const TitleScene=()=>{
  const f=useCurrentFrame();
  return <AbsoluteFill style={{background:"radial-gradient(circle at 74% 42%,rgba(14,165,233,.20),transparent 34%),linear-gradient(135deg,#0F172A,#1E293B)"}}>
    <Grain/><Brand/>
    <div style={{position:"absolute",left:105,top:210,width:1400,opacity:fade(f)}}>
      <div style={{fontFamily:"Arial,Helvetica,sans-serif",color:C.red,fontSize:21,fontWeight:900,letterSpacing:2.5}}>HEALTHCARE AUTOPSY — EPISODE 1</div>
      <div style={{fontFamily:"Georgia,Times New Roman,serif",fontSize:91,lineHeight:1.01,color:C.white,fontWeight:700,marginTop:26,letterSpacing:-2}}>Theranos: When the Blood Test Didn’t Work</div>
      <div style={{width:165,height:4,background:C.blue,marginTop:36}}/>
      <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:26,color:"#CBD5E1",marginTop:28}}>Rising and Falling in Healthcare</div>
    </div>
  </AbsoluteFill>;
};

const Workflow=()=>{
  const f=useCurrentFrame();
  const steps=["PATIENT","BLOOD SAMPLE","ANALYZER","VALIDATION","RESULT","CLINICIAN DECISION"];
  return <AbsoluteFill style={{background:C.navy}}><Grain/><Brand/>
    <div style={{position:"absolute",left:90,top:120,right:90}}>
      <div style={{fontFamily:"Georgia,serif",fontSize:57,fontWeight:700,color:C.white}}>In laboratory medicine, the test is the product.</div>
      <div style={{display:"flex",alignItems:"center",gap:13,marginTop:105}}>
        {steps.map((s,i)=>{
          const on=f>i*13;
          const val=s==="VALIDATION";
          return <React.Fragment key={s}>
            <div style={{flex:1,minHeight:155,border:"2px solid "+(val?C.red:C.line),background:val?"rgba(220,38,38,.10)":"rgba(30,41,59,.82)",display:"flex",alignItems:"center",justifyContent:"center",padding:17,textAlign:"center",opacity:on?1:.25,fontFamily:"Arial,Helvetica,sans-serif",fontSize:24,fontWeight:800,letterSpacing:.7,color:C.white}}>{s}</div>
            {i<steps.length-1?<div style={{fontSize:30,color:C.gray}}>→</div>:null}
          </React.Fragment>
        })}
      </div>
      <div style={{marginTop:58,fontFamily:"Arial,Helvetica,sans-serif",fontSize:36,fontWeight:900,color:C.red}}>Accuracy and reproducibility are not optional.</div>
    </div>
  </AbsoluteFill>;
};

const Checklist=()=>{
  const f=useCurrentFrame();
  const items=["Specimen type","Accuracy","Precision","Quality control","Reportable range","Reference interval"];
  return <AbsoluteFill style={{background:"linear-gradient(135deg,#0F172A,#172554)"}}><Grain/><Brand/>
    <div style={{position:"absolute",left:100,top:130}}>
      <div style={{fontFamily:"Georgia,serif",fontSize:58,fontWeight:700,color:C.white}}>What clinicians need from a laboratory result</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:22,marginTop:70,width:1450}}>
        {items.map((x,i)=><div key={x} style={{display:"flex",alignItems:"center",gap:20,padding:"24px 30px",border:"1px solid "+C.line,background:"rgba(30,41,59,.70)",opacity:f>i*10?1:.25}}>
          <div style={{width:34,height:34,borderRadius:99,border:"3px solid "+C.blue,display:"flex",alignItems:"center",justifyContent:"center",fontSize:18,color:C.white}}>✓</div>
          <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:31,fontWeight:700,color:"#E2E8F0"}}>{x}</div>
        </div>)}
      </div>
    </div>
  </AbsoluteFill>;
};

const CompareSpecimens=()=>(
  <AbsoluteFill style={{background:C.navy}}><Grain/><Brand/>
    <div style={{position:"absolute",left:100,top:130,right:100}}>
      <div style={{fontFamily:"Georgia,serif",fontSize:56,fontWeight:700,color:C.white}}>Capillary and venous specimens are not automatically interchangeable.</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:28,marginTop:70}}>
        <div style={{padding:45,border:"1px solid "+C.line,background:"rgba(30,41,59,.72)"}}>
          <div style={{fontSize:23,fontWeight:900,color:C.blue,letterSpacing:1.8}}>CAPILLARY COLLECTION</div>
          <div style={{fontSize:31,lineHeight:1.5,color:"#E2E8F0",marginTop:25}}>Technique · hemolysis · handling · volume · specimen type</div>
        </div>
        <div style={{padding:45,border:"1px solid "+C.line,background:"rgba(30,41,59,.72)"}}>
          <div style={{fontSize:23,fontWeight:900,color:C.blue,letterSpacing:1.8}}>VENOUS COLLECTION</div>
          <div style={{fontSize:31,lineHeight:1.5,color:"#E2E8F0",marginTop:25}}>A separate specimen pathway requiring validated performance characteristics</div>
        </div>
      </div>
      <div style={{marginTop:56,padding:"28px 34px",borderLeft:"5px solid "+C.red,background:"rgba(220,38,38,.08)",fontFamily:"Georgia,serif",fontSize:35,lineHeight:1.35,color:C.white}}>“Was the technology validated well enough for clinicians to make decisions from the results?”</div>
    </div>
  </AbsoluteFill>
);

const Timeline=()=>{
  const f=useCurrentFrame();
  const items=[["2003","Theranos founded"],["2013","Walgreens partnership announced"],["2015–16","Public scrutiny and regulatory action"],["2018","SEC civil charges; federal indictment"],["2022","Separate jury verdicts"]];
  return <AbsoluteFill style={{background:C.navy}}><Grain/><Brand/>
    <div style={{position:"absolute",left:105,top:140,right:105}}>
      <div style={{fontFamily:"Georgia,serif",fontSize:58,fontWeight:700,color:C.white}}>The chronology matters.</div>
      <div style={{height:3,background:C.line,position:"absolute",left:25,right:25,top:245}}/>
      <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:15,marginTop:120}}>
        {items.map(([year,label],i)=><div key={year} style={{opacity:f>i*10?1:.22,position:"relative",paddingTop:40}}>
          <div style={{position:"absolute",top:-3,left:0,width:22,height:22,borderRadius:99,background:i>=2?C.red:C.blue,border:"4px solid "+C.navy}}/>
          <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:31,fontWeight:900,color:C.white}}>{year}</div>
          <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:23,lineHeight:1.35,color:"#CBD5E1",marginTop:15,maxWidth:280}}>{label}</div>
        </div>)}
      </div>
    </div>
  </AbsoluteFill>;
};

const EvidenceCard=({label,headline,body,source}:{label:string;headline:string;body:string;source:string})=>{
  const f=useCurrentFrame();
  return <AbsoluteFill style={{background:"linear-gradient(135deg,#0F172A,#1E293B)"}}><Grain/><Brand/>
    <div style={{position:"absolute",left:150,top:145,width:1370,opacity:fade(f)}}>
      <SourceChip>{source}</SourceChip>
      <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:22,fontWeight:900,letterSpacing:2.2,color:C.red,marginTop:56}}>{label}</div>
      <div style={{fontFamily:"Georgia,serif",fontSize:68,lineHeight:1.08,fontWeight:700,color:C.white,marginTop:18}}>{headline}</div>
      <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:31,lineHeight:1.48,color:"#CBD5E1",marginTop:32,maxWidth:1280}}>{body}</div>
    </div>
  </AbsoluteFill>;
};

const Verdicts=()=>(
  <AbsoluteFill style={{background:C.navy}}><Grain/><Brand/>
    <div style={{position:"absolute",left:95,top:115,right:95}}>
      <SourceChip>U.S. Department of Justice / federal court records</SourceChip>
      <div style={{fontFamily:"Georgia,serif",fontSize:54,fontWeight:700,color:C.white,marginTop:38}}>Separate trials. Separate verdicts.</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:30,marginTop:48}}>
        <div style={{border:"1px solid "+C.line,background:"rgba(30,41,59,.77)",padding:40}}>
          <div style={{fontSize:20,fontWeight:900,letterSpacing:2,color:C.blue}}>ELIZABETH HOLMES — JANUARY 2022</div>
          <div style={{fontFamily:"Georgia,serif",fontSize:39,lineHeight:1.28,color:C.white,marginTop:22}}>Jury convicted on four investor-fraud-related counts.</div>
          <div style={{fontSize:26,lineHeight:1.45,color:"#CBD5E1",marginTop:23}}>Patient-related counts submitted to the jury resulted in acquittals. The jury did not reach unanimous verdicts on three additional investor counts.</div>
          <div style={{fontSize:25,fontWeight:900,color:C.red,marginTop:28}}>Sentence: 135 months</div>
        </div>
        <div style={{border:"1px solid "+C.line,background:"rgba(30,41,59,.77)",padding:40}}>
          <div style={{fontSize:20,fontWeight:900,letterSpacing:2,color:C.blue}}>RAMESH “SUNNY” BALWANI — JULY 2022</div>
          <div style={{fontFamily:"Georgia,serif",fontSize:39,lineHeight:1.28,color:C.white,marginTop:22}}>A separate jury convicted on all twelve counts in his case.</div>
          <div style={{fontSize:26,lineHeight:1.45,color:"#CBD5E1",marginTop:23}}>Those counts included investor- and patient-related fraud offenses.</div>
          <div style={{fontSize:25,fontWeight:900,color:C.red,marginTop:28}}>Sentence: 155 months</div>
        </div>
      </div>
    </div>
  </AbsoluteFill>
);

const ThreeColumns=()=>(
  <AbsoluteFill style={{background:C.navy}}><Grain/><Brand/>
    <div style={{position:"absolute",left:80,top:135,right:80}}>
      <div style={{fontFamily:"Georgia,serif",fontSize:57,fontWeight:700,color:C.white}}>Keep the categories separate.</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:22,marginTop:68}}>
        {[
          ["BUSINESS FAILURE","The claimed laboratory model did not become a reliable, scalable clinical-testing business."],
          ["REGULATORY & COMPLIANCE FAILURE","Laboratory oversight and quality findings brought regulatory consequences."],
          ["CRIMINAL CONVICTIONS","Juries returned the specific fraud convictions described in the public record."]
        ].map(([h,b],i)=><div key={h} style={{minHeight:430,padding:"36px 34px",border:"1px solid "+(i===2?C.red:C.line),background:i===2?"rgba(220,38,38,.07)":"rgba(30,41,59,.75)"}}>
          <div style={{fontSize:21,fontWeight:900,letterSpacing:1.5,color:i===2?C.red:C.blue}}>{h}</div>
          <div style={{fontFamily:"Georgia,serif",fontSize:35,lineHeight:1.36,color:C.white,marginTop:35}}>{b}</div>
        </div>)}
      </div>
    </div>
  </AbsoluteFill>
);

const HostPlaceholder=()=>(
  <AbsoluteFill style={{background:"radial-gradient(circle at 50% 45%,rgba(14,165,233,.12),transparent 36%),#0F172A"}}><Grain/><Brand/>
    <div style={{position:"absolute",inset:0,display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column"}}>
      <div style={{border:"1px solid "+C.line,padding:"52px 78px",background:"rgba(30,41,59,.70)",textAlign:"center"}}>
        <div style={{fontSize:22,fontWeight:900,letterSpacing:2.3,color:C.red}}>FINAL HOST SHOT PENDING</div>
        <div style={{fontFamily:"Georgia,serif",fontSize:55,fontWeight:700,color:C.white,marginTop:22}}>HOST FOOTAGE REQUIRED — DR. MIKE DANIELS</div>
        <div style={{fontSize:24,color:C.gray,marginTop:20}}>No AI likeness or substitute presenter used.</div>
      </div>
    </div>
  </AbsoluteFill>
);

const Sources=()=>(
  <AbsoluteFill style={{background:C.navy}}><Grain/>
    <div style={{position:"absolute",left:110,top:85,right:110}}>
      <div style={{fontFamily:"Arial,Helvetica,sans-serif",fontSize:21,fontWeight:900,letterSpacing:2.2,color:C.blue}}>WORKS CITED / PRIMARY PUBLIC RECORDS</div>
      <div style={{fontFamily:"Georgia,serif",fontSize:48,fontWeight:700,color:C.white,marginTop:20}}>Healthcare Autopsy: Theranos</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"15px 60px",marginTop:44,fontFamily:"Arial,Helvetica,sans-serif",fontSize:25,lineHeight:1.45,color:"#CBD5E1"}}>
        {["U.S. Department of Justice","U.S. Securities and Exchange Commission","Centers for Medicare & Medicaid Services / HHS","Federal court records and sentencing materials","Walgreens corporate releases","WHO specimen-collection guidance"].map(x=><div key={x}>• {x}</div>)}
      </div>
      <div style={{borderTop:"1px solid "+C.line,marginTop:44,paddingTop:30,fontSize:22,lineHeight:1.45,color:C.gray,fontFamily:"Arial,Helvetica,sans-serif"}}>This episode is educational commentary based on public records and cited sources.</div>
      <div style={{fontSize:28,fontWeight:900,color:C.white,marginTop:28,fontFamily:"Arial,Helvetica,sans-serif"}}>Brought to you by ThePodiatryVoice.com</div>
    </div>
  </AbsoluteFill>
);

const CaptionLayer=({captions}:{captions:Caption[]})=>{
  const f=useCurrentFrame();
  const t=f/FPS;
  const cue=captions.find(c=>t>=c.start&&t<c.end);
  if(!cue)return null;
  return <div style={{position:"absolute",left:170,right:170,bottom:54,display:"flex",justifyContent:"center",zIndex:90,pointerEvents:"none"}}>
    <div style={{maxWidth:1500,padding:"13px 21px",background:"rgba(15,23,42,.82)",boxShadow:"0 8px 28px rgba(0,0,0,.22)",borderRadius:5,fontFamily:"Arial,Helvetica,sans-serif",fontSize:37,lineHeight:1.23,fontWeight:700,textAlign:"center",color:C.white,textShadow:"0 2px 5px rgba(0,0,0,.8)"}}>
      {cue.lines.map((l,i)=><React.Fragment key={i}>{i>0?<br/>:null}{l}</React.Fragment>)}
    </div>
  </div>;
};

const Scene=({from,duration,children}:{from:number;duration:number;children:React.ReactNode})=>(
  <Sequence from={sec(from)} durationInFrames={sec(duration)}>{children}</Sequence>
);

const Film=({captions,musicPresent}:Props)=>(
  <AbsoluteFill style={{background:C.navy}}>
    <Audio src={staticFile("assets/audio/narration_full.wav")} volume={1}/>
    {musicPresent?<Audio src={staticFile("assets/music/documentary_underscore.mp3")} volume={0.055} loop/>:null}

    <Scene from={0} duration={6}><VideoBed src="assets/video/broll-blood-collection.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="The promise" title="Faster. Cheaper. Less painful."/></Scene>
    <Scene from={6} duration={6}><VideoBed src="assets/video/broll-lab-analyzer.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="Laboratory medicine" title="A result is only useful if it is reliable."/></Scene>
    <Scene from={12} duration={8}><TitleScene/></Scene>

    <Scene from={20} duration={15}><VideoBed src="assets/video/broll-silicon-valley.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="2003" title="A simple promise with enormous appeal." body="Broad blood testing from a very small sample, often a finger prick."/></Scene>
    <Scene from={35} duration={15}><VideoBed src="assets/video/broll-venipuncture.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="The consumer appeal" title="Less blood. Less friction." body="The clinical question was whether the laboratory science could support the promise."/></Scene>
    <Scene from={50} duration={15}><VideoBed src="assets/video/broll-pharmacy.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="2013" title="Retail scale arrived before the clinical questions were settled." body="Walgreens and Theranos announced a long-term partnership."/></Scene>

    <Scene from={65} duration={30}><Workflow/></Scene>
    <Scene from={95} duration={30}><VideoBed src="assets/video/broll-lab-tech.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="Quality control" title="Clinicians need more than a number." body="They need confidence in method, specimen, reproducibility, controls, ranges, and reference intervals."/></Scene>
    <Scene from={125} duration={20}><Checklist/></Scene>
    <Scene from={145} duration={20}><CompareSpecimens/></Scene>

    <Scene from={165} duration={20}><Timeline/></Scene>
    <Scene from={185} duration={20}><EvidenceCard label="REGULATORY FINDING" headline="CMS found immediate jeopardy to patient health." body="The finding addressed practices and procedures in the Theranos clinical laboratory. It is a regulatory finding, not a criminal verdict, and it does not mean every Theranos test was wrong." source="CMS / HHS"/></Scene>
    <Scene from={205} duration={20}><EvidenceCard label="COMMERCIAL + CIVIL DEVELOPMENTS" headline="Walgreens ended the relationship. The SEC later brought civil fraud charges." body="Walgreens cited voided test results and CMS rejection of Theranos's correction plan. In 2018, the SEC alleged misleading statements about the technology, business, and financial performance." source="Walgreens corporate release / SEC"/></Scene>
    <Scene from={225} duration={25}><Verdicts/></Scene>
    <Scene from={250} duration={20}><ThreeColumns/></Scene>

    <Scene from={270} duration={15}><VideoBed src="assets/video/broll-quiet-lab.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="2018" title="Theranos wound down." body="The case became a warning about commercial momentum outrunning clinical verification."/></Scene>
    <Scene from={285} duration={30}><VideoBed src="assets/video/broll-clinician-review.mp4" label="Wikimedia Commons documentary footage"/><BigText eyebrow="The healthcare lesson" title="Innovation has to survive clinical reality." body="A compelling pitch, major investors, media attention, and a national retail partner do not substitute for a test that works reliably."/></Scene>
    <Scene from={315} duration={20}><HostPlaceholder/></Scene>
    <Scene from={335} duration={10}><Sources/></Scene>

    <CaptionLayer captions={captions}/>
  </AbsoluteFill>
);

const Root=()=>(
  <Composition
    id="TheranosHealthcareAutopsy"
    component={Film}
    durationInFrames={sec(345)}
    fps={FPS}
    width={1920}
    height={1080}
    defaultProps={{captions:[],musicPresent:true}}
  />
);

registerRoot(Root);
