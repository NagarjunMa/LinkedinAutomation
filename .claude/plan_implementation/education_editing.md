# Education Individual Editing Implementation Plan

## Current Issue
The education section in the profile page (`frontend/src/app/dashboard/profile/page.tsx`) only allows bulk editing of all education entries at once. Users cannot edit individual education records.

## Requirement
Add pencil icons to each education entry that allow individual editing with:
- Individual edit mode per entry
- Add new education button at the bottom
- Delete confirmation for each entry

## Current Implementation Analysis
From the profile page analysis:
- Education is displayed using `EducationSection` component
- Current edit mode switches the entire section to edit mode
- State managed with `editingSection` and `setEditingSection`
- Education data stored in `educationHistory` state array

## Proposed Solution

### 1. New State Management
Replace the global education edit state with individual entry tracking:

```typescript
const [editingEducationId, setEditingEducationId] = useState<string | null>(null)
const [addingNewEducation, setAddingNewEducation] = useState(false)
```

### 2. Component Structure Update

#### Individual Edit State
Each education entry will have:
- View mode: Display data with pencil icon button
- Edit mode: Inline editing form for that specific entry
- Save/Cancel buttons for individual entries

#### New Education Entry
- "Add Education" button at the bottom
- When clicked, adds empty entry in edit mode
- Can be cancelled to remove the empty entry

### 3. UI Changes

#### In View Mode (for each education entry):
```
[Education Entry Card]
  [Degree Name]                    [📝 Edit Icon]
  [University Name]
  [Field of Study, Location]
  [Start Date - End Date]
```

#### In Edit Mode (for specific entry):
```
[Education Entry Card - Edit Mode]
  [Degree Input Field]             [💾 Save] [❌ Cancel]
  [University Input Field]
  [Field of Study Input Field]
  [Location Input Field]
  [Start Date] [End Date]          [🗑️ Delete]
```

#### At Bottom of Section:
```
[+ Add Education] button
```

### 4. Implementation Steps

1. **Modify EducationSection component**:
   - Replace global edit state with individual entry IDs
   - Add pencil icons to each entry in view mode
   - Implement inline editing for specific entries

2. **Add individual entry editing logic**:
   - Save individual entries without affecting others
   - Cancel editing to revert changes for that entry only
   - Delete individual entries with confirmation

3. **Add new education functionality**:
   - "Add Education" button that creates a new empty entry in edit mode
   - Proper state management for new vs existing entries

### 5. Code Changes Required

#### Update EducationSection function signature:
```typescript
function EducationSection({
  education,
  setEducation,
  editingEducationId,
  setEditingEducationId,
  onSaveEducation,
  onDeleteEducation,
  saving
}: {
  education: Education[];
  setEducation: (edu: Education[]) => void;
  editingEducationId: string | null;
  setEditingEducationId: (id: string | null) => void;
  onSaveEducation: (education: Education) => void;
  onDeleteEducation: (id: string) => void;
  saving: boolean;
})
```

#### Individual Entry Component:
```typescript
function EducationEntry({
  education,
  index,
  isEditing,
  onStartEdit,
  onSave,
  onCancel,
  onDelete,
  onChange
}: EducationEntryProps)
```

### 6. Benefits
- Better UX: Users can edit individual entries without losing other data
- Reduced cognitive load: Focus on one entry at a time
- Faster editing: No need to scroll through all entries to edit one
- Safer operations: Less chance of accidental data loss

### 7. Technical Considerations
- Maintain backward compatibility with existing API endpoints
- Ensure proper error handling for individual save operations
- Add proper TypeScript interfaces for the new component props
- Implement proper loading states for individual save operations

## File Changes Required
- `frontend/src/app/dashboard/profile/page.tsx` - Main profile page component
- May need to extract education components into separate files for better organization