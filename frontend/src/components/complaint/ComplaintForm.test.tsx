import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore, combineReducers } from "@reduxjs/toolkit";
import { ComplaintForm } from "./ComplaintForm";
import complaintFormReducer from "../../features/complaint/complaintFormSlice";
import "@testing-library/jest-dom";

const rootReducer = combineReducers({
  complaintForm: complaintFormReducer,
});

const renderWithProviders = (
  ui: React.ReactElement,
  preloadedState: any = {}
) => {
  const store = configureStore({
    reducer: rootReducer,
    preloadedState,
  });

  return render(<Provider store={store}>{ui}</Provider>);
};

describe("ComplaintForm", () => {
  it("should render complaint fields", () => {
    renderWithProviders(<ComplaintForm />);
    expect(screen.getByText("Complaint Structured Data")).toBeInTheDocument();
    expect(screen.getByText("Product Name")).toBeInTheDocument();
    expect(screen.getByText("Complaint Date")).toBeInTheDocument();
  });
});
