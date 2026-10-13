import test from 'node:test';
import assert from 'node:assert/strict';
import { CRITERIA, evaluateNexus } from './core.mjs';
const absent = Object.fromEntries(CRITERIA.map(c => [c, false]));
test('five absent findings produce negative NEXUS', () => {
  assert.equal(evaluateNexus(absent).classification, 'NEXUS_NEGATIVE');
});
for (const criterion of CRITERIA) {
  test(`present ${criterion} prevents clearance`, () => {
    const result = evaluateNexus({ ...absent, [criterion]: true });
    assert.equal(result.classification, 'NEXUS_POSITIVE');
    assert.deepEqual(result.positive, [criterion]);
  });
}
test('missing evidence is not a negative rule', () => {
  assert.equal(evaluateNexus({ ...absent, intoxication: null }).classification, 'INCOMPLETE');
});
test('known positive stays positive despite another unknown', () => {
  assert.equal(evaluateNexus({ ...absent, intoxication: true, distracting_injury: null }).classification, 'NEXUS_POSITIVE');
});
test('older adult warning does not change criterion result', () => {
  const result = evaluateNexus(absent, 80);
  assert.equal(result.classification, 'NEXUS_NEGATIVE');
  assert.match(result.ageCaution, /65/);
});
test('invalid age rejected', () => {
  assert.throws(() => evaluateNexus(absent, 200), RangeError);
});
