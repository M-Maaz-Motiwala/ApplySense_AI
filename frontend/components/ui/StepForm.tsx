"use client";

import { ReactNode } from "react";
import { Button } from "./Button";

interface StepFormProps {
  steps: string[];
  currentStep: number;
  onNext: () => void;
  onBack: () => void;
  onSubmit: () => void;
  isNextDisabled?: boolean;
  isLoading?: boolean;
  children: ReactNode;
}

export function StepForm({
  steps,
  currentStep,
  onNext,
  onBack,
  onSubmit,
  isNextDisabled = false,
  isLoading = false,
  children
}: StepFormProps) {
  const isLastStep = currentStep === steps.length;

  return (
    <div className="w-full max-w-4xl mx-auto glass-panel p-8">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          {steps.map((step, i) => (
            <span key={step} className={`text-xs font-bold uppercase ${currentStep > i ? "text-indigo-600" : "text-slate-400"}`}>
              {step}
            </span>
          ))}
        </div>
        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
          <div 
            className="bg-indigo-600 h-full transition-all duration-300 ease-in-out" 
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
          />
        </div>
      </div>

      <h1 className="text-2xl font-bold text-slate-900 mb-6">
        Step {currentStep}: {steps[currentStep - 1]}
      </h1>

      <div className="min-h-[400px]">
        {children}
      </div>

      {/* Footer Actions */}
      <div className="flex justify-between mt-8 pt-6 border-t border-slate-200">
        <Button 
          variant="ghost" 
          onClick={onBack} 
          disabled={currentStep === 1 || isLoading}
        >
          Back
        </Button>
        
        {!isLastStep ? (
          <Button 
            variant="primary" 
            onClick={onNext} 
            disabled={isNextDisabled || isLoading}
          >
            Next Step &rarr;
          </Button>
        ) : (
          <Button 
            variant="primary" 
            onClick={onSubmit} 
            loading={isLoading}
            disabled={isNextDisabled}
          >
            Complete Profile
          </Button>
        )}
      </div>
    </div>
  );
}
