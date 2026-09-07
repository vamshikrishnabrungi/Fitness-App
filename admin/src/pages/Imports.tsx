import { useEffect, useRef, useState } from 'react';
import { CheckCircle2, FileUp, RefreshCw } from 'lucide-react';
import {
  commitStructuredDataset, commitWorkbook, getDatasetStatus, importDetail, listImports,
  previewExerciseDocument, previewStructuredDataset, type DatasetStatus, type SourceImport, type SourceImportDetail,
} from '../lib/api';
import { ErrorNotice, Header, Modal, PageGuide } from '../components/Studio';

type Kind='exercises'|'training_templates'|'sport_priority_matrix'|'training_policies';
type Preview={id:string;version:number;status:string;row_count:number;summary:Record<string,number>};
const cards:{kind:Kind;number:number;title:string;description:string;accept:string;multiple:boolean;expected:string}[]=[
 {kind:'exercises',number:1,title:'Exercise catalogue',description:'Creates new exercises and creates a new immutable version for matching stable exercise codes.',accept:'.csv',multiple:false,expected:'curated_exercises.csv'},
 {kind:'training_templates',number:2,title:'Four-week references',description:'Stores category- and level-specific four-week progressions linked to canonical exercise IDs.',accept:'.json',multiple:true,expected:'Select phase_01 through phase_09 JSON files together'},
 {kind:'sport_priority_matrix',number:3,title:'Sport priority matrix',description:'Stores sport, role/event, phase and goal category rankings plus session block order.',accept:'.csv',multiple:false,expected:'sport_role_phase_goal_priority_matrix.csv'},
 {kind:'training_policies',number:4,title:'Mode and phase policies',description:'Stores each sport’s primary training mode and the four phase-dose policies.',accept:'.json',multiple:true,expected:'Select sport_mode_policy.json and phase_dose_policies.json together'},
];

export function Imports(){
 const [history,setHistory]=useState<SourceImport[]>([]),[status,setStatus]=useState<DatasetStatus|null>(null),[previews,setPreviews]=useState<Partial<Record<Kind,Preview>>>({}),[detail,setDetail]=useState<SourceImportDetail|null>(null),[error,setError]=useState(''),[working,setWorking]=useState<Kind|null>(null);
 const inputs=useRef<Partial<Record<Kind,HTMLInputElement|null>>>({});
 const load=async()=>{const [imports,current]=await Promise.all([listImports(),getDatasetStatus()]);setHistory(imports);setStatus(current)};
 useEffect(()=>{void load().catch(reason=>setError((reason as Error).message))},[]);
 async function upload(kind:Kind,files:File[]){if(!files.length)return;setWorking(kind);setError('');try{const preview=kind==='exercises'?await previewExerciseDocument(files[0]):await previewStructuredDataset(kind,files);setPreviews(value=>({...value,[kind]:preview}));await load()}catch(reason){setError((reason as Error).message)}finally{setWorking(null)}}
 async function commit(kind:Kind){const preview=previews[kind];if(!preview)return;setWorking(kind);setError('');try{if(kind==='exercises')await commitWorkbook(preview);else await commitStructuredDataset(preview);setPreviews(value=>({...value,[kind]:{...preview,status:'committed'}}));await load()}catch(reason){setError((reason as Error).message)}finally{setWorking(null)}}
 const counts=status?.counts;
 const countFor=(kind:Kind)=>kind==='exercises'?counts?.exercises:kind==='training_templates'?counts?.training_templates:kind==='sport_priority_matrix'?counts?.sport_priorities:(counts?.sport_mode_policies??0)+(counts?.phase_dose_policies??0);
 return <>
  <Header eyebrow="TRAINING DATA" title="Data imports" description="Preview, validate and commit the four datasets used by workout generation." actions={<button className="secondary" onClick={()=>void load()}><RefreshCw size={16}/>Refresh status</button>}/>
  <PageGuide title="How to import training data" steps={["Upload in order: exercises, four-week references, sport priority matrix, then policies.","Preview validates every row and does not alter active data.","Open validation details if errors are reported. Commit is blocked until every row is valid.","Re-uploading the same file is idempotent. Changed canonical content creates a new immutable version."]}/>
  <ErrorNotice message={error}/>
  <section className="dataset-grid">{cards.map(card=>{const preview=previews[card.kind];const invalid=Number(preview?.summary.errors??preview?.summary.rows_with_errors??0);return <article className="dataset-card" key={card.kind}>
   <div className="dataset-number">{card.number}</div><div><h2>{card.title}</h2><p>{card.description}</p><small>{card.expected}</small></div>
   <div className="dataset-count"><strong>{countFor(card.kind)??'—'}</strong><span>stored records</span></div>
   {preview&&<div className={`dataset-preview ${invalid?'invalid':'valid'}`}><strong>{preview.row_count} rows · {invalid?`${invalid} invalid`:'validation passed'}</strong><span>{JSON.stringify(preview.summary)}</span></div>}
   <div className="row-actions"><button className="secondary" disabled={working===card.kind} onClick={()=>inputs.current[card.kind]?.click()}><FileUp size={16}/>{preview?'Choose again':'Choose file'}</button>{preview&&preview.status!=='committed'&&<button className="primary" disabled={working===card.kind||invalid>0} onClick={()=>void commit(card.kind)}><CheckCircle2 size={16}/>Commit to PostgreSQL</button>}</div>
   <input hidden ref={node=>{inputs.current[card.kind]=node}} type="file" accept={card.accept} multiple={card.multiple} onChange={event=>void upload(card.kind,Array.from(event.target.files??[]))}/>
  </article>})}</section>
  <section className="panel spaced"><div className="section-heading"><div><h2>Import history</h2><p>Content hashes make repeated uploads safe.</p></div></div><table><thead><tr><th>DATASET</th><th>FILES</th><th>ROWS</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>{history.map(row=><tr key={row.id}><td><strong>{row.source_type?.replaceAll('_',' ')??'exercise import'}</strong></td><td>{row.source_name}</td><td>{row.row_count}</td><td><span className={`status ${row.status==='committed'?'ready':'draft'}`}>{row.status}</span></td><td><button className="secondary" onClick={()=>importDetail(row.id).then(setDetail).catch(reason=>setError((reason as Error).message))}>Validation details</button></td></tr>)}</tbody></table></section>
  {detail&&<Modal title={detail.source_name} eyebrow="IMPORT VALIDATION" onClose={()=>setDetail(null)}><div className="candidate-list import-rows">{detail.rows.map(row=><div className="import-row" key={row.id}><strong>{row.source_reference}</strong><span className={`status ${row.validation_errors.length?'draft':'ready'}`}>{row.validation_errors.length?'Invalid':'Valid'}</span>{row.validation_errors.length>0&&<p>{row.validation_errors.join(' · ')}</p>}</div>)}</div></Modal>}
 </>;
}
