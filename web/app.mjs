import { CRITERIA, evaluateNexus } from './core.mjs';

const form = document.querySelector('#assessment');
const result = document.querySelector('#result');
const labels = Object.fromEntries(CRITERIA.map(key => [key, form.elements[key].dataset.label]));

form.addEventListener('submit', event => {
  event.preventDefault();
  const values = Object.fromEntries(CRITERIA.map(name => {
    const input = form.elements[name].value;
    return [name, input === 'present' ? true : input === 'absent' ? false : null];
  }));
  const ageText = form.elements.age.value.trim();
  const age = ageText === '' ? null : Number(ageText);
  result.replaceChildren();
  try {
    const outcome = evaluateNexus(values, age);
    const heading = document.createElement('h2');
    heading.textContent = outcome.classification === 'NEXUS_NEGATIVE'
      ? 'NEXUS negative · Low-risk criteria met'
      : outcome.classification === 'NEXUS_POSITIVE'
        ? 'NEXUS positive · Cannot clear clinically'
        : 'Incomplete assessment · Cannot clear clinically';
    const guidance = document.createElement('p');
    guidance.textContent = outcome.guidance;
    result.append(heading, guidance);
    for (const [name, findings] of [['Present findings', outcome.positive], ['Not assessed', outcome.missing]]) {
      if (findings.length) {
        const line = document.createElement('p');
        line.textContent = `${name}: ${findings.map(key => labels[key]).join('; ')}.`;
        result.append(line);
      }
    }
    if (outcome.ageCaution) {
      const caution = document.createElement('p');
      caution.textContent = outcome.ageCaution;
      result.append(caution);
    }
    result.dataset.status = outcome.classification;
  } catch (error) {
    result.dataset.status = 'INCOMPLETE';
    result.textContent = error.message;
  }
  result.hidden = false;
  result.focus();
});

form.addEventListener('reset', () => {
  result.hidden = true;
  result.replaceChildren();
  delete result.dataset.status;
});
