import { Activity, AppWindow, BookOpen, Database, Dumbbell, Goal, LayoutTemplate, Network, Trophy, Users } from 'lucide-react';
import type { ReactNode } from 'react';

const groups=[
 ['TRAINING',[[Dumbbell,'Exercises'],[LayoutTemplate,'Workout templates'],[Network,'Programs'],[Goal,'Sports & goals'],[BookOpen,'Sport articles'],[Database,'Data imports']]],
 ['CUSTOMERS',[[Users,'Users']]],
 ['OPERATIONS',[[Trophy,'Run clubs'],[Activity,'Activity processing']]],
 ['SETTINGS',[[AppWindow,'App settings']]],
] as const;
export function Shell({children,section,onSection,operator,onSignOut}:{children:ReactNode;section:string;onSection:(x:string)=>void;operator:string;onSignOut:()=>void}){
 return <div className="app-shell"><aside><div className="brand"><span className="mark">R</span><div><strong>RUNLETE</strong><small>ADMIN STUDIO</small></div></div><nav aria-label="Admin Studio navigation">{groups.map(([label,items])=><div className="nav-group" key={label}><label>{label}</label>{items.map(([Icon,name])=><button aria-current={section===name?'page':undefined} className={section===name?'active':''} onClick={()=>onSection(name)} key={name}><Icon size={20}/><span>{name}</span></button>)}</div>)}</nav><div className="operator"><span className="online"/><div><strong>{operator}</strong><small>Authenticated session</small><button onClick={onSignOut}>Sign out</button></div></div></aside><main>{children}</main></div>
}
