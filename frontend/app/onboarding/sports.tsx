import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { RUNNING_EVENTS } from '../../src/data/running';

export default function RunningGoalScreen(){
 const router=useRouter(); const insets=useSafeAreaInsets(); const store=useOnboardingStore();
 const [event,setEvent]=useState(store.target_event||''); const [distance,setDistance]=useState(store.target_distance?.toString()||'');
 const [date,setDate]=useState(store.target_date||''); const [time,setTime]=useState(store.target_time); const [unit,setUnit]=useState(store.distance_unit);
 const race=store.goal_type==='target_race'; const custom=event==='trail'||event==='ultra';
 const next=()=>{store.setGoal({target_event:event||null,target_distance:custom&&distance?Number(distance):null,target_date:date||null,target_time:time,distance_unit:unit});router.push('/onboarding/experience');};
 return <View style={[coachLayout.container,{paddingTop:insets.top}]}><CoachProgress step={2}/><ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content}>
 <CoachCard icon="navigate" eyebrow="RUNNING PROFILE" title={race?'Choose your target event.':'How do you prefer to run?'} subtitle="Your event changes the balance of endurance, speed, strength, and recovery.">
 <CoachSection title={race?'Target event':'Primary running style'}/><View style={coachLayout.chipGrid}>{RUNNING_EVENTS.map(x=><CoachChip key={x.code} label={x.label} selected={event===x.code} onPress={()=>setEvent(x.code)}/>)}</View>
 {custom&&<><CoachSection title={`Target distance (${unit})`}/><CoachField value={distance} onChangeText={setDistance} placeholder={unit==='km'?'50':'31'} keyboardType="decimal-pad"/></>}
 <CoachSection title="Distance units"/><View style={coachLayout.chipGrid}><CoachChip label="Kilometres" selected={unit==='km'} onPress={()=>setUnit('km')}/><CoachChip label="Miles" selected={unit==='mi'} onPress={()=>setUnit('mi')}/></View>
 {race&&<><CoachSection title="Race date" meta="Optional"/><CoachField value={date} onChangeText={setDate} placeholder="YYYY-MM-DD"/><CoachSection title="Target time" meta="Optional"/><CoachField value={time} onChangeText={setTime} placeholder="HH:MM:SS"/></>}
 </CoachCard></ScrollView><CoachBottom bottomInset={insets.bottom} disabled={!event||(custom&&!distance)} onPress={next}/></View>;
}
