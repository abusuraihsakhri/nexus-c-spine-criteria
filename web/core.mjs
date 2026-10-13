// Pure implementation of the five NEXUS findings. True = present, false = absent.
export const CRITERIA = Object.freeze([
  'midline_tenderness',
  'intoxication',
  'altered_alertness',
  'focal_neurologic_deficit',
  'distracting_injury'
]);

export function evaluateNexus(findings, age = null) {
  const positive = [];
  const missing = [];
  for (const name of CRITERIA) {
    const value = findings[name];
    if (value === true) positive.push(name);
    else if (value !== false) missing.push(name);
  }
  let classification, guidance;
  if (positive.length) {
    classification = 'NEXUS_POSITIVE';
    guidance = 'NEXUS cannot support clinical clearance. Assess the need for cervical-spine imaging.';
  } else if (missing.length) {
    classification = 'INCOMPLETE';
    guidance = 'Complete all five assessments. Do not clear the cervical spine with an incomplete rule.';
  } else {
    classification = 'NEXUS_NEGATIVE';
    guidance = 'All five low-risk criteria are met. Imaging may be unnecessary if clinically appropriate.';
  }
  if (age !== null && (!Number.isInteger(age) || age < 0 || age > 120)) {
    throw new RangeError('Age must be an integer from 0 to 120.');
  }
  const ageCaution = age !== null && (age < 16 || age >= 65)
    ? 'Evidence is less certain in children and adults aged 65 or older; do not rely on NEXUS alone.'
    : '';
  return { classification, positive, missing, guidance, ageCaution };
}
