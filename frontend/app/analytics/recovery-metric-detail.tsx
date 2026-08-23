import React, { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
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

const labels: Record<string, string> = { readiness: 'Readiness', sleep: 'Sleep', stress: 'Stress', 'resting-hr': 'Resting heart rate', hrv: 'HRV' };

export default function RecoveryMetricDetailScreen() {
  const router = useRouter();
  const { type = 'readiness' } = useLocalSearchParams<{ type?: string }>();
  const [data, setData] = useState<HealthSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { setData(await api.get<HealthSummary>('/health/summary')); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Health data is unavailable.'); }
    finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { void load(); }, [load]));

  const metric = resolveMetric(type, data);
  return <SafeAreaView style={styles.container}>
    <View style={styles.header}><TouchableOpacity onPress={() => router.back()} style={styles.back}><Ionicons name="chevron-back" size={23} color={colors.textPrimary}/></TouchableOpacity><View><Text style={styles.title}>{labels[type] || 'Recovery metric'}</Text><Text style={styles.subtitle}>Recorded and connected-health data</Text></View></View>
    <ScrollView contentContainerStyle={styles.content}>
      {loading ? <ActivityIndicator color={colors.brand}/> : error ? <Panel title="Unable to load" body={error}/> : <>
        <View style={styles.hero}><Text style={styles.value}>{metric.value}</Text><Text style={styles.unit}>{metric.unit}</Text><Text style={styles.source}>{metric.source}</Text></View>
        {!metric.available && <Panel title="No measurement" body="Runlete will not substitute a sample value. Add a daily check-in or connect an approved health source to populate this metric."/>}
        <Panel title="Safety boundary" body="This view reports the stored measurement and its source. It does not diagnose illness, predict injury, or replace qualified medical advice."/>
        {!!data?.open_pain_reports && <Panel title="Open pain reports" body={`${data.open_pain_reports} report${data.open_pain_reports === 1 ? '' : 's'} still require review or resolution.`}/>}
      </>}
    </ScrollView>
  </SafeAreaView>;
}

function resolveMetric(type:string,data:HealthSummary|null) {
  if (!data) return {value:'—',unit:'',source:'No data',available:false};
  if(type==='readiness') return {value:data.readiness ?? '—',unit:data.readiness ? '/ 5':'',source:'Daily check-in',available:data.readiness!=null};
  if(type==='stress') return {value:data.stress ?? '—',unit:data.stress ? '/ 5':'',source:'Daily check-in',available:data.stress!=null};
  if(type==='sleep') return {value:data.sleep_minutes!=null?(data.sleep_minutes/60).toFixed(1):'—',unit:data.sleep_minutes!=null?'hours':'',source:data.connected_metrics.sleep_duration_min?.provider || 'Daily check-in',available:data.sleep_minutes!=null};
  const code=type==='hrv'?'hrv_rmssd_ms':'resting_hr_bpm'; const item=data.connected_metrics[code];
  return {value:item?.value ?? '—',unit:item?.unit || '',source:item?`${item.provider} · ${new Date(item.measured_at).toLocaleString()}`:'No connected measurement',available:Boolean(item)};
}

function Panel({title,body}:{title:string;body:string}) { return <View style={styles.panel}><Text style={styles.panelTitle}>{title}</Text><Text style={styles.body}>{body}</Text></View>; }
const styles=StyleSheet.create({container:{flex:1,backgroundColor:colors.background},header:{flexDirection:'row',alignItems:'center',gap:12,padding:spacing.page},back:{width:40,height:40,borderRadius:20,alignItems:'center',justifyContent:'center',backgroundColor:colors.surface},title:{fontSize:20,fontWeight:'900',color:colors.textPrimary},subtitle:{fontSize:10.5,color:colors.textSecondary,marginTop:2},content:{padding:spacing.page,paddingTop:4},hero:{borderRadius:22,backgroundColor:colors.surface,padding:28,alignItems:'center'},value:{fontSize:50,fontWeight:'900',color:colors.textPrimary},unit:{fontSize:13,fontWeight:'800',color:colors.textSecondary,marginTop:3},source:{fontSize:10,color:colors.textTertiary,marginTop:10},panel:{marginTop:14,borderRadius:18,backgroundColor:'#EDF3FF',padding:18},panelTitle:{fontWeight:'900',color:'#334D75'},body:{color:'#415474',fontSize:11.5,lineHeight:17,marginTop:6}});
