import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import type { Decision, Evidence } from '@/features/career-coach/api';

export const ownershipLabels = {
  individual: 'Individual', shared: 'Shared', team: 'Team', unknown: 'Unknown',
} satisfies Record<Evidence['ownership'], string>;

export function EvidenceEdit({ item, disabled, save, cancel }: {
  item: Evidence; disabled: boolean; save: (decision: Decision) => void; cancel: () => void;
}) {
  const [claim, setClaim] = useState(item.claim);
  const [ownership, setOwnership] = useState(item.ownership);
  const [scope, setScope] = useState(item.scope ?? '');
  const [method, setMethod] = useState(item.measurement?.method ?? '');
  const [measurementScope, setMeasurementScope] = useState(item.measurement?.scope ?? '');
  const [estimated, setEstimated] = useState(item.measurement?.estimated ?? false);

  const decision: Decision = { action: 'edit', revision: item.revision };
  const claimChanged = claim.trim() !== item.claim;
  if (claimChanged) decision.claim = claim.trim();
  if (ownership !== item.ownership) decision.ownership = ownership;
  if (scope.trim() !== (item.scope ?? '')) decision.scope = scope.trim() || null;
  const hasMeasurement = Boolean(method.trim() || measurementScope.trim());
  const measurementChanged = method.trim() !== (item.measurement?.method ?? '') ||
    measurementScope.trim() !== (item.measurement?.scope ?? '') || estimated !== (item.measurement?.estimated ?? false);
  if (measurementChanged && (hasMeasurement || item.measurement)) {
    decision.measurement = hasMeasurement ? { method: method.trim(), scope: measurementScope.trim(), estimated } : null;
  }
  const valid = claim.trim() && (!hasMeasurement || (method.trim() && measurementScope.trim()));
  const changed = Object.keys(decision).length > 2;

  return (
    <form className="space-y-3" onSubmit={event => {
      event.preventDefault();
      if (!disabled && valid && changed) save(decision);
    }}>
      <p className="text-sm text-muted-foreground">Editing confirmed evidence returns it to review. Add measurement details if the claim includes a number you can explain.</p>
      {claimChanged && item.measurement && !measurementChanged &&
        <p className="text-sm text-muted-foreground">Saving new wording clears the previous measurement details. Review the measurement fields if they should accompany the edit.</p>}
      <fieldset disabled={disabled} className="min-w-0 space-y-3">
        <label className="block text-sm font-medium">Claim
          <Textarea autoFocus className="mt-1" required value={claim} maxLength={4000} onChange={event => setClaim(event.target.value)} />
        </label>
        <label className="block text-sm font-medium">Ownership
          <select className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-2" value={ownership}
            onChange={event => setOwnership(event.target.value as Evidence['ownership'])}>
            {Object.entries(ownershipLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium">Contribution scope
          <Input className="mt-1" value={scope} maxLength={200} onChange={event => setScope(event.target.value)} />
        </label>
        <label className="block text-sm font-medium">Measurement method
          <Input className="mt-1" value={method} required={hasMeasurement} maxLength={200} onChange={event => setMethod(event.target.value)} />
        </label>
        <label className="block text-sm font-medium">Measurement scope
          <Input className="mt-1" value={measurementScope} required={hasMeasurement} maxLength={200} onChange={event => setMeasurementScope(event.target.value)} />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={estimated} disabled={!hasMeasurement} onChange={event => setEstimated(event.target.checked)} />
          Estimated measurement
        </label>
      </fieldset>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={disabled || !valid || !changed}>Save edit</Button>
        <Button type="button" variant="outline" disabled={disabled} onClick={cancel}>Cancel edit</Button>
      </div>
    </form>
  );
}
