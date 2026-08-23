import type * as React from 'react';
import { useState } from 'react';
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

export default function App(){
 const [section,setSection]=useState('Exercises');
 const pages:Record<string,React.ReactNode>={'Exercises':<Methods/>,'Workout templates':<Recipes/>,'Programs':<Programs/>,'Sports & goals':<SportKnowledge/>,'Data imports':<Imports/>,'Users':<UsersPage/>,'Run clubs':<Clubs/>,'Activity processing':<Processing/>,'App settings':<Platform/>};
 return <Shell section={section} onSection={setSection} operator="Local operator">{pages[section]}</Shell>;
}
