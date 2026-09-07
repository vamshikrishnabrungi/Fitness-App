import type * as React from 'react';
import { useEffect, useState } from 'react';
import { Shell } from './components/Shell';
import { Methods } from './pages/Methods';
import { Recipes } from './pages/Recipes';
import { UsersPage } from './pages/Users';
import { Programs } from './pages/Programs';
import { SportKnowledge } from './pages/SportKnowledge';
import { Clubs } from './pages/Clubs';
import { Processing } from './pages/Processing';
import { Platform } from './pages/Platform';
import { Imports } from './pages/Imports';
import { SportContent } from './pages/SportContent';
import { adminSession, clearAdminSession, logoutAdmin, requestOtp, setAdminSession, verifyOtp } from './lib/api';

function SignIn({onSignedIn}:{onSignedIn:()=>void}){
 const [email,setEmail]=useState('');const [challenge,setChallenge]=useState('');const [code,setCode]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 const send=async()=>{setBusy(true);setError('');try{const result=await requestOtp(email);setChallenge(result.challenge_id);}catch(e){setError(e instanceof Error?e.message:'Unable to send code');}finally{setBusy(false);}};
 const verify=async()=>{setBusy(true);setError('');try{const result=await verifyOtp(challenge,email,code);if(!result.user.roles.some(role=>['content_editor','content_publisher','moderator','platform_admin'].includes(role)))throw new Error('This account does not have Admin Studio access.');setAdminSession(result);onSignedIn();}catch(e){clearAdminSession();setError(e instanceof Error?e.message:'Unable to sign in');}finally{setBusy(false);}};
 return <main className="login-page"><section className="login-card"><span className="mark">R</span><p className="eyebrow">RUNLETE ADMIN STUDIO</p><h1>Secure sign in</h1><p>Use an account that has an assigned administration role.</p><label>Email<input type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} disabled={Boolean(challenge)}/></label>{challenge&&<label>Six-digit code<input inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={e=>setCode(e.target.value.replace(/\D/g,''))}/></label>}{error&&<div className="notice danger" role="alert">{error}</div>}<button className="primary" disabled={busy||!email||Boolean(challenge&&code.length!==6)} onClick={challenge?verify:send}>{busy?'Please wait…':challenge?'Verify and continue':'Send sign-in code'}</button>{challenge&&<button className="secondary" disabled={busy} onClick={()=>{setChallenge('');setCode('');setError('');}}>Use another email</button>}</section></main>;
}

export default function App(){
 const [section,setSection]=useState('Exercises');
 const [session,setSession]=useState(()=>adminSession());
 useEffect(()=>{const expired=()=>setSession(null);window.addEventListener('runlete-admin-session-expired',expired);return()=>window.removeEventListener('runlete-admin-session-expired',expired);},[]);
 if(!session)return <SignIn onSignedIn={()=>setSession(adminSession())}/>;
 const pages:Record<string,React.ReactNode>={'Exercises':<Methods/>,'Workout templates':<Recipes/>,'Programs':<Programs/>,'Sports & goals':<SportKnowledge/>,'Sport articles':<SportContent/>,'Data imports':<Imports/>,'Users':<UsersPage/>,'Run clubs':<Clubs/>,'Activity processing':<Processing/>,'App settings':<Platform/>};
 return <Shell section={section} onSection={setSection} operator={session.user.display_name} onSignOut={async()=>{try{await logoutAdmin();}finally{clearAdminSession();setSession(null);}}}>{pages[section]}</Shell>;
}
