import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { ComplaintFields, DuplicateStatus, DuplicateMatch } from "../../types/complaint";

export interface ComplaintFormState {
  currentForm: ComplaintFields;
  changedFields: string[];
  completenessPct: number;
  missingFields: string[];
  duplicateStatus: DuplicateStatus;
  duplicateMatches: DuplicateMatch[];
  complaintId: string | null;
}

const initialState: ComplaintFormState = {
  currentForm: {},
  changedFields: [],
  completenessPct: 0,
  missingFields: [],
  duplicateStatus: "UNIQUE",
  duplicateMatches: [],
  complaintId: null,
};

const complaintFormSlice = createSlice({
  name: "complaintForm",
  initialState,
  reducers: {
    applyFormPatch(
      state,
      action: PayloadAction<{
        patch?: ComplaintFields;
        changedFields: string[];
        completenessPct: number;
        missingFields: string[];
        duplicateStatus?: DuplicateStatus;
        duplicateMatches?: DuplicateMatch[];
        complaintId?: string;
      }>
    ) {
      const { patch, changedFields, completenessPct, missingFields, duplicateStatus, duplicateMatches } =
        action.payload;
        
      if (patch) {
        const safePatch = Object.fromEntries(
          Object.entries(patch).filter(([_, v]) => v !== null && v !== undefined)
        );
        state.currentForm = {
          ...state.currentForm,
          ...safePatch,
        };
      }
      
      state.changedFields = changedFields;
      state.completenessPct = completenessPct;
      state.missingFields = missingFields;
      if (duplicateStatus) state.duplicateStatus = duplicateStatus;
      if (duplicateMatches) state.duplicateMatches = duplicateMatches;
      if (action.payload.complaintId) {
        state.complaintId = action.payload.complaintId;
      }
    },
  },
});

export const { applyFormPatch } = complaintFormSlice.actions;
export default complaintFormSlice.reducer;
