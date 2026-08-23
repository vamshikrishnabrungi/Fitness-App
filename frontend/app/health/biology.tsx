import React, { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface HealthSummary {
  readiness: number | null;
  sleep_minutes: number | null;
  stress: number | null;
  open_pain_reports: number;
  connected_metrics: Record<string, { value: number; unit: string; measured_at: string; provider: string }>;
}

export default function BiologyScreen() {
  const router = useRouter();
  const [data, setData] = useState<HealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { setData(await api.get<HealthSummary>('/health/summary')); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Health metrics are unavailable.'); }
    finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { void load(); }, [load]));

  const resting = data?.connected_metrics.resting_hr_bpm;
  const hrv = data?.connected_metrics.hrv_rmssd_ms;
  return <SafeAreaView style={styles.container}>
    <View style={styles.header}><TouchableOpacity onPress={() => router.back()} style={styles.back}><Ionicons name="chevron-back" size={23} color={colors.textPrimary}/></TouchableOpacity><View><Text style={styles.title}>Health measurements</Text><Text style={styles.subtitle}>Check-ins and connected sources</Text></View></View>
    <ScrollView contentContainerStyle={styles.content}>
      {loading ? <ActivityIndicator color={colors.brand}/> : error ? <Notice title="Unable to load" body={error}/> : <>
        <View style={styles.grid}>
          <Metric label="Readiness" value={data?.readiness != null ? `${data.readiness} / 5` : '—'} source="Daily check-in"/>
          <Metric label="Sleep" value={data?.sleep_minutes != null ? `${(data.sleep_minutes / 60).toFixed(1)} h` : '—'} source={data?.connected_metrics.sleep_duration_min?.provider || 'Daily check-in'}/>
          <Metric label="Resting HR" value={resting ? `${resting.value} ${resting.unit}` : '—'} source={resting?.provider || 'No measurement'}/>
          <Metric label="HRV (RMSSD)" value={hrv ? `${hrv.value} ${hrv.unit}` : '—'} source={hrv?.provider || 'No measurement'}/>
        </View>
        <Notice title="No inferred values" body="Runlete displays only measurements you entered or imported with consent. Missing VO₂ max, body composition, or baseline values remain missing until a supported source provides them."/>
        <Notice title="Health boundary" body="These measurements support training context. They are not a diagnosis, treatment recommendation, or substitute for professional medical care."/>
      </>}
    </ScrollView>
  </SafeAreaView>;
}

function Metric({label,value,source}:{label:string;value:string;source:string}) { return <View style={styles.metric}><Text style={styles.metricLabel}>{label}</Text><Text style={styles.metricValue}>{value}</Text><Text style={styles.metricSource}>{source}</Text></View>; }
function Notice({title,body}:{title:string;body:string}) { return <View style={styles.notice}><Text style={styles.noticeTitle}>{title}</Text><Text style={styles.noticeBody}>{body}</Text></View>; }
const styles=StyleSheet.create({container:{flex:1,backgroundColor:colors.background},header:{flexDirection:'row',gap:12,alignItems:'center',padding:spacing.page},back:{width:40,height:40,borderRadius:20,alignItems:'center',justifyContent:'center',backgroundColor:colors.surface},title:{fontSize:20,fontWeight:'900',color:colors.textPrimary},subtitle:{fontSize:10.5,color:colors.textSecondary,marginTop:2},content:{padding:spacing.page,paddingTop:4,paddingBottom:50},grid:{flexDirection:'row',flexWrap:'wrap',gap:10},metric:{width:'48%',minHeight:125,borderRadius:18,padding:16,backgroundColor:colors.surface,justifyContent:'center'},metricLabel:{fontSize:10.5,fontWeight:'800',color:colors.textSecondary},metricValue:{fontSize:24,fontWeight:'900',color:colors.textPrimary,marginTop:7},metricSource:{fontSize:9.5,color:colors.textTertiary,marginTop:7},notice:{borderRadius:18,padding:18,backgroundColor:'#EDF3FF',marginTop:14},noticeTitle:{fontWeight:'900',color:'#334D75'},noticeBody:{fontSize:11.5,lineHeight:17,color:'#415474',marginTop:6}});
