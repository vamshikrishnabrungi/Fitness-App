import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { RunnerLevel, useOnboardingStore } from '../../src/store/onboardingStore';

const LEVELS:RunnerLevel[]=['beginner','intermediate','advanced'];
export default function ExperienceScreen(){const router=useRouter();const insets=useSafeAreaInsets();const store=useOnboardingStore();
 const [level,setLevel]=useState(store.experience_level);const [runs,setRuns]=useState(String(store.runs_per_week));const [weekly,setWeekly]=useState(String(store.weekly_distance));const [longest,setLongest]=useState(String(store.longest_recent_run));const [interruption,setInterruption]=useState(store.training_interruption);
 const next=()=>{store.setBaseline({experience_level:level,runs_per_week:Number(runs)||0,weekly_distance:Number(weekly)||0,longest_recent_run:Number(longest)||0,training_interruption:interruption});router.push('/onboarding/schedule');};
 const detailFlow=store.goal_type!=='start_running';
 return <View style={[coachLayout.container,{paddingTop:insets.top}]}><CoachProgress step={detailFlow?3:2} total={detailFlow?5:4}/><ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content}><CoachCard icon="speedometer" eyebrow="CURRENT BASELINE" title="Where are you starting from?" subtitle="Use a normal recent week. Estimates are fine, and new runners can enter zero.">
 <CoachSection title="Running experience"/><View style={coachLayout.chipGrid}>{LEVELS.map(x=><CoachChip key={x} label={x} selected={level===x} onPress={()=>setLevel(x)}/>)}</View>
 <CoachSection title="Recent training"/><View style={coachLayout.fieldGrid}><CoachField style={coachLayout.halfField} label="Runs per week" value={runs} onChangeText={setRuns} placeholder="3" keyboardType="number-pad"/><CoachField style={coachLayout.halfField} label={`Weekly ${store.distance_unit}`} value={weekly} onChangeText={setWeekly} placeholder="20" keyboardType="decimal-pad"/><CoachField style={coachLayout.halfField} label={`Longest run (${store.distance_unit})`} value={longest} onChangeText={setLongest} placeholder="8" keyboardType="decimal-pad"/></View>
 <CoachSection title="Time away from running"/><View style={coachLayout.chipGrid}>{['none','under_1_month','1_to_3_months','over_3_months'].map(x=><CoachChip key={x} label={x.replaceAll('_',' ')} selected={interruption===x} onPress={()=>setInterruption(x)}/>)}</View>
 </CoachCard></ScrollView><CoachBottom bottomInset={insets.bottom} onPress={next}/></View>}
