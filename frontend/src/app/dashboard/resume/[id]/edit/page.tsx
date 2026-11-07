// frontend/src/app/dashboard/resume/[id]/edit/page.tsx
"use client";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { ResumeRenderer } from '@/components/resume/resume-renderer';
import { RewriteModal } from '@/components/resume/rewrite-modal';
import { AtsTab } from '@/components/resume/ats-tab';
import { useEvaluateResume, useCreateVersion } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/auth-context';
import { resumeDocKey, resumeEditorKey } from '@/lib/resume-cache';
import type {
  ResumeDocumentJSON, EvaluationResponse, Bullet, ChangeItem,
} from '@/app/lib/api';

export default function ResumeEditPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  return user?.id ? <ResumeEditor key={resumeDocKey(user.id, id)} id={id} userId={user.id} /> : null;
}

function ResumeEditor({ id, userId }: { id: string; userId: string }) {
  const router = useRouter();
  const { toast } = useToast();
  const [doc, setDoc] = useState<ResumeDocumentJSON | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [country, setCountry] = useState('US');
  const [activeBullet, setActiveBullet] = useState<Bullet | null>(null);
  const [pendingChanges, setPendingChanges] = useState<ChangeItem[]>([]);
  const [versionId, setVersionId] = useState<string>();
  const [working, setWorking] = useState(false);
  const operationInFlight = useRef(false);
  const mounted = useRef(false);
  const activeFindings = useMemo(() => evaluation?.bullet_flags.filter(
    (flag) => flag.bullet_id === activeBullet?.id,
  ) ?? [], [evaluation, activeBullet?.id]);

  const evaluate = useEvaluateResume();
  const createVersion = useCreateVersion();
  const docKey = resumeDocKey(userId, id);
  const editorKey = resumeEditorKey(userId, id);

  useLayoutEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  // On mount, fetch the doc from the upload response cached in sessionStorage,
  // or refuse to render (the user must go through /dashboard/resume to upload).
  useEffect(() => {
    const cached = sessionStorage.getItem(editorKey);
    if (cached) {
      try {
        const editor = JSON.parse(cached);
        setVersionId(editor.versionId);
        setPendingChanges(editor.pendingChanges);
      } catch {
        sessionStorage.removeItem(editorKey);
      }
    }
    const raw = sessionStorage.getItem(docKey);
    if (raw) setDoc(JSON.parse(raw));
  }, [docKey, editorKey]);

  useEffect(() => {
    if (doc) {
      sessionStorage.setItem(docKey, JSON.stringify(doc));
      sessionStorage.setItem(editorKey, JSON.stringify({ versionId, pendingChanges }));
    }
  }, [docKey, editorKey, doc, versionId, pendingChanges]);

  const savePendingChanges = async () => {
    if (pendingChanges.length === 0) return versionId;
    const result = await createVersion.mutateAsync({
      resumeId: id,
      body: { ...(versionId ? { parent_version_id: versionId } : {}), change_set: pendingChanges },
    });
    setVersionId(result.version_id);
    setPendingChanges([]);
    return result.version_id;
  };

  const runEvaluate = async () => {
    if (operationInFlight.current || activeBullet) return;
    if (!targetRole || targetRole.length < 2) {
      toast({ title: 'Set a target role first', variant: 'destructive' });
      return;
    }
    operationInFlight.current = true;
    setWorking(true);
    try {
      const currentVersion = await savePendingChanges();
      if (!mounted.current) return;
      const res = await evaluate.mutateAsync({ resumeId: id, targetRole,
        ...(currentVersion ? { versionId: currentVersion } : {}) });
      setEvaluation(res);
    } catch (e: any) {
      if (e?.status === 402) {
        toast({
          title: 'Out of credits',
          description: 'Top up to continue.',
          variant: 'destructive',
        });
      } else {
        toast({ title: 'Evaluation failed', description: e?.message, variant: 'destructive' });
      }
    } finally {
      operationInFlight.current = false;
      setWorking(false);
    }
  };

  const findBullet = (bulletId: string): Bullet | null => {
    if (!doc) return null;
    for (const exp of doc.experience) for (const b of exp.bullets) if (b.id === bulletId) return b;
    for (const p of doc.projects) for (const b of p.bullets) if (b.id === bulletId) return b;
    return null;
  };

  const onBulletClick = async (bulletId: string) => {
    if (operationInFlight.current || activeBullet) return;
    operationInFlight.current = true;
    setWorking(true);
    try {
      await savePendingChanges();
      const b = findBullet(bulletId);
      if (b) setActiveBullet(b);
    } catch (error: any) {
      toast({ title: 'Save failed', description: error?.message, variant: 'destructive' });
    } finally {
      operationInFlight.current = false;
      setWorking(false);
    }
  };

  const onAcceptRewrite = (bulletId: string, newText: string) => {
    setPendingChanges((prev) => [
      ...prev.filter((c) => !(c.type === 'bullet_update' && c.bullet_id === bulletId)),
      { type: 'bullet_update', bullet_id: bulletId, new_text: newText },
    ]);
    // Optimistically update the rendered doc.
    setDoc((prev) => {
      if (!prev) return prev;
      const next = structuredClone(prev) as ResumeDocumentJSON;
      for (const exp of next.experience)
        for (const b of exp.bullets) if (b.id === bulletId) b.text = newText;
      for (const p of next.projects)
        for (const b of p.bullets) if (b.id === bulletId) b.text = newText;
      return next;
    });
  };

  const onSaveVersion = async () => {
    if (operationInFlight.current || activeBullet || pendingChanges.length === 0) return;
    operationInFlight.current = true;
    setWorking(true);
    try {
      await savePendingChanges();
      toast({ title: 'Version saved' });
    } catch (e: any) {
      toast({ title: 'Save failed', description: e?.message, variant: 'destructive' });
    } finally {
      operationInFlight.current = false;
      setWorking(false);
    }
  };

  if (!doc) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <p className="text-sm opacity-70 mb-3">No resume loaded.</p>
        <Button onClick={() => router.push('/dashboard/resume')}>Upload one</Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardContent className="pt-6 flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-40">
            <Label htmlFor="role">Target role</Label>
            <Input id="role" value={targetRole} disabled={working || !!activeBullet} onChange={(e) => setTargetRole(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="country">Country</Label>
            <select
              id="country"
              className="border rounded px-2 py-1 block"
              value={country}
              disabled={working || !!activeBullet}
              onChange={(e) => setCountry(e.target.value)}
            >
              <option value="US">US</option>
              <option value="IN">IN</option>
            </select>
          </div>
          <Button onClick={runEvaluate} disabled={working || !!activeBullet}>
            {evaluate.isPending ? 'Evaluating…' : evaluation ? 'Re-evaluate' : 'Evaluate (1 credit)'}
          </Button>
          <Button
            variant="outline"
            onClick={onSaveVersion}
            disabled={pendingChanges.length === 0 || working || !!activeBullet}
          >
            Save version ({pendingChanges.length})
          </Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="resume">
        <TabsList>
          <TabsTrigger value="resume">Resume</TabsTrigger>
          <TabsTrigger value="ats" disabled={!evaluation}>Document checks</TabsTrigger>
        </TabsList>
        <TabsContent value="resume">
          {evaluation && (
            <section aria-label="Content findings" className="text-sm mb-6 space-y-3">
              <h2 className="font-semibold">Content findings</h2>
              <p>Model-assisted feedback, not a hiring assessment. Verify suggestions against your actual experience; document checks are separate.</p>
              <p>Findings describe the last evaluation. Re-evaluate after editing. Document checks describe the uploaded file.</p>
              {evaluation.summary_critique && (
                <p>{evaluation.summary_critique}</p>
              )}
              {evaluation.score_explanation.length > 0 && (
                <ul className="space-y-3">
                  {evaluation.score_explanation.map((finding, index) => (
                    <li key={`${finding.category}-${index}`}>
                      <h3 className="font-semibold capitalize">{finding.category.replaceAll('_', ' ')}</h3>
                      <p>{finding.reason}</p>
                      <p>{finding.before_applying_action}</p>
                    </li>
                  ))}
                </ul>
              )}
              {evaluation.top_actions_before_applying.length > 0 && (
                <div>
                  <h3 className="font-semibold">Suggested next steps</h3>
                  <ul className="list-disc ml-5">
                    {evaluation.top_actions_before_applying.map((action, index) => <li key={index}>{action}</li>)}
                  </ul>
                </div>
              )}
              {!evaluation.summary_critique && evaluation.score_explanation.length === 0 && evaluation.top_actions_before_applying.length === 0 && (
                <p>No content findings returned. This is not a hiring assessment.</p>
              )}
            </section>
          )}
          <ResumeRenderer
            doc={doc}
            flags={evaluation?.bullet_flags ?? []}
            onBulletClick={onBulletClick}
          />
        </TabsContent>
        <TabsContent value="ats">
          {evaluation && <AtsTab evaluation={evaluation} />}
        </TabsContent>
      </Tabs>

      <RewriteModal
        open={!!activeBullet}
        onOpenChange={(o) => { if (!o) setActiveBullet(null); }}
        resumeId={id}
        bullet={activeBullet}
        targetRole={targetRole}
        country={country}
        versionId={versionId}
        findings={activeFindings}
        onAccept={onAcceptRewrite}
      />
    </div>
  );
}
