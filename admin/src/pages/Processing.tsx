import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { operationsOverview, type OperationsOverview } from '../lib/api';
import { Header, PageGuide } from '../components/Studio';

const cards: [keyof OperationsOverview, string, string][] = [
  ['activities_processing', 'ACTIVITIES PROCESSING', 'Uploaded, processing or provisional'],
  ['imports_processing', 'IMPORTS IN FLIGHT', 'Awaiting upload, queued or processing'],
  ['food_processing', 'FOOD ANALYSIS', 'Queued or processing'],
  ['outbox_unpublished', 'OUTBOX WAITING', 'Durable events not yet published'],
  ['consumer_retries', 'CONSUMER RETRIES', 'Events awaiting another delivery'],
  ['jobs_queued', 'OPERATIONS JOBS', 'Queued or processing'],
];

export function Processing(){
  const [data,setData]=useState<OperationsOverview|null>(null),[error,setError]=useState('');
  const load=()=>{setError('');return operationsOverview().then(setData).catch(reason=>setError(reason instanceof Error?reason.message:'Could not load processing health.'))};
  useEffect(()=>{void load()},[]);
  return <><Header eyebrow="OPERATIONS" title="Activity processing" description="Monitor runs, imports and food analyses that are processing or require attention." actions={<button className="icon-button quiet" aria-label="Refresh processing status" onClick={()=>void load()}><RefreshCw size={18}/></button>}/><PageGuide title="activity processing" steps={["Processing counts show work that is still underway; this is normal shortly after an upload.","Rejected activities failed a terminal quality or anti-cheat decision and are not included in competition.","Failed imports or food analyses require corrected input or a retry after the dependency recovers.","Event and generic job counts represent background updates such as notifications, exports and recalculation."]}/>{error&&<div className="notice">{error}</div>}<section className="stats operations-stats">{data&&cards.map(([key,label,help])=><div key={key}><small>{label}</small><strong>{data[key]}</strong><span className={data[key]?'warn':'success'}>{help}</span></div>)}</section>{data&&<section className="panel"><table><thead><tr><th>ITEMS REQUIRING ATTENTION</th><th>COUNT</th><th>WHAT IT MEANS</th></tr></thead><tbody><tr><td><strong>Rejected activities</strong></td><td>{data.activities_rejected}</td><td>Run quality or competition validation did not pass.</td></tr><tr><td><strong>Failed activity imports</strong></td><td>{data.imports_failed}</td><td>The uploaded file was invalid or processing exhausted its retries.</td></tr><tr><td><strong>Failed food analyses</strong></td><td>{data.food_failed}</td><td>Image analysis or result validation could not finish.</td></tr><tr><td><strong>Other failed jobs</strong></td><td>{data.jobs_failed}</td><td>Exports, retention or other scheduled work requires attention.</td></tr></tbody></table></section>}</>;
}
