import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { X } from 'lucide-react';

export function Header({eyebrow,title,description,actions}:{eyebrow:string;title:string;description:string;actions?:ReactNode}){
  return <header className="topbar"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div><div className="row-actions">{actions}</div></header>;
}

export function Tabs({value,onChange,items}:{value:string;onChange:(value:string)=>void;items:{value:string;label:string;count?:number}[]}){
  return <div className="tabs" role="tablist">{items.map(item=><button role="tab" aria-selected={value===item.value} className={value===item.value?'active':''} onClick={()=>onChange(item.value)} key={item.value}>{item.label}{item.count!==undefined&&<span>{item.count}</span>}</button>)}</div>;
}

export function Modal({title,eyebrow='DRAFT CONTENT',children,onClose,wide=true,resource=false}:{title:string;eyebrow?:string;children:ReactNode;onClose:()=>void;wide?:boolean;resource?:boolean}){
  const ref=useRef<HTMLElement>(null);useEffect(()=>{const previous=document.activeElement as HTMLElement|null;const key=(event:KeyboardEvent)=>event.key==='Escape'&&onClose();document.addEventListener('keydown',key);ref.current?.focus();return()=>{document.removeEventListener('keydown',key);previous?.focus()}},[onClose]);
  return <div className={`modal-backdrop ${resource?'resource-editor-backdrop':''}`} role="presentation" onMouseDown={event=>!resource&&event.target===event.currentTarget&&onClose()}><section ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} className={`decision-modal form-grid ${wide?'wide':''} ${resource?'resource-editor':''}`}><button aria-label="Close" type="button" className="icon-close" onClick={onClose}><X/></button><span className="eyebrow">{resource?'EXERCISE LIBRARY / EDIT':eyebrow}</span><h2>{title}</h2>{children}</section></div>;
}

export function PageGuide({title,steps,notes=[],open=false}:{title:string;steps:string[];notes?:string[];open?:boolean}){return <details className="page-guide" open={open}><summary>How to use {title}</summary><div><ol>{steps.map(step=><li key={step}>{step}</li>)}</ol>{notes.map(note=><p key={note}>{note}</p>)}</div></details>}
export function Busy({label='Loading…'}:{label?:string}){return <div className="loading-state"><span className="spinner"/>{label}</div>}
export function SuccessNotice({message}:{message:string}){return message?<div className="notice success-notice" role="status">{message}</div>:null}

export function Empty({title,description}:{title:string;description:string}){return <div className="table-empty"><strong>{title}</strong><p>{description}</p></div>}
export function ErrorNotice({message,onDismiss}:{message:string;onDismiss?:()=>void}){return message?<div className="notice" role="alert"><span>{message}</span>{onDismiss&&<button onClick={onDismiss}>Dismiss</button>}</div>:null}
export const csv=(value:FormDataEntryValue|null)=>String(value??'').split(',').map(item=>item.trim()).filter(Boolean);
export const json=(value:FormDataEntryValue|null,fallback:unknown={})=>{const text=String(value??'').trim();return text?JSON.parse(text):fallback};
export const readable=(value:string)=>value.replaceAll('_',' ').replace(/\b\w/g,letter=>letter.toUpperCase());
