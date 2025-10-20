/**
 * Maps category codes to human-readable display names
 */
export const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
  'Alzheimer': "Alzheimer's Disease",
  'Cardiological': 'Cardiovascular Health',
  'T2D': 'Type 2 Diabetes',
  'Obesity_BMI': 'Obesity & Metabolic Health',
  'CKD': 'Chronic Kidney Disease',
  'AF': 'Atrial Fibrillation',
  'Inflammation': 'Inflammation Markers',
  'Parkinson': "Parkinson's Disease",
  'Lung Cancer': 'Lung Cancer',
  'Colorectal Cancer': 'Colorectal Cancer',
  'Breast Cancer': 'Breast Cancer',
  'Prostate Cancer': 'Prostate Cancer',
  'Pancreatic Cancer': 'Pancreatic Cancer',
  'Melanoma': 'Melanoma',
  'Osteoarthritis': 'Osteoarthritis',
  'Osteoporosis': 'Osteoporosis',
  'Sarcopenia': 'Sarcopenia & Muscle Health',
  'Longevity': 'Exceptional Longevity',
  'General Longevity': 'General Longevity',
};

/**
 * Get the display name for a category code
 * @param categoryCode The category code from the API
 * @returns The human-readable display name
 */
export function getCategoryDisplayName(categoryCode: string): string {
  return CATEGORY_DISPLAY_NAMES[categoryCode] || categoryCode;
}
