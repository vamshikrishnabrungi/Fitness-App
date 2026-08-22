import React, { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface FitnessResponse { current: { fitness: number; fatigue: number; form: number } }

export default function TrainingLoadDetailScreen() {
  const router = useRouter();
  const [data, setData] = useState<FitnessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { setData(await api.get<FitnessResponse>('/training/fitness')); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Training load is unavailable.'); }
    finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { void load(); }, [load]));

  return <SafeAreaView style={styles.container}>
    <View style={styles.header}><TouchableOpacity onPress={() => router.back()} style={styles.back}><Ionicons name="chevron-back" size={23} color={colors.textPrimary}/></TouchableOpacity><View><Text style={styles.title}>Training load</Text><Text style={styles.subtitle}>Completed workout records only</Text></View></View>
    <ScrollView contentContainerStyle={styles.content}>
      {loading ? <ActivityIndicator color={colors.brand}/> : error ? <View style={styles.panel}><Text style={styles.panelTitle}>No load result</Text><Text style={styles.body}>{error}</Text></View> : data && <>
        <View style={styles.grid}>
          <Metric label="28-day daily average" value={data.current.fitness}/>
          <Metric label="7-day daily average" value={data.current.fatigue}/>
          <Metric label="Form difference" value={data.current.form}/>
        </View>
        <View style={styles.panel}><Text style={styles.panelTitle}>How to read this</Text><Text style={styles.body}>These are arithmetic summaries of completed session load. They are not a diagnosis, readiness score, injury prediction, or instruction to increase training. If there are no completed workouts, zero is the truthful result.</Text></View>
      </>}
    </ScrollView>
  </SafeAreaView>;
}

function Metric({label,value}:{label:string;value:number}) { return <View style={styles.metric}><Text style={styles.value}>{Number(value || 0).toFixed(1)}</Text><Text style={styles.label}>{label}</Text></View>; }

const styles=StyleSheet.create({
  container:{flex:1,backgroundColor:colors.background},header:{flexDirection:'row',alignItems:'center',gap:12,padding:spacing.page},back:{width:40,height:40,borderRadius:20,alignItems:'center',justifyContent:'center',backgroundColor:colors.surface},title:{fontSize:20,fontWeight:'900',color:colors.textPrimary},subtitle:{fontSize:10.5,color:colors.textSecondary,marginTop:2},content:{padding:spacing.page,paddingTop:5},grid:{gap:10},metric:{backgroundColor:colors.surface,borderRadius:18,padding:20},value:{fontSize:34,fontWeight:'900',color:colors.textPrimary},label:{fontSize:11,color:colors.textSecondary,marginTop:4},panel:{marginTop:16,backgroundColor:'#EDF3FF',borderRadius:18,padding:18},panelTitle:{fontWeight:'900',color:'#334D75'},body:{color:'#415474',fontSize:11.5,lineHeight:17,marginTop:7}
});
