import assert from 'node:assert/strict';
import {decisionDelta} from '../../frontend/modules/decision-metrics.js';

assert.deepEqual(decisionDelta('123.45','141.97'),{amount:'18.52',percentage:'15.00'});
assert.deepEqual(decisionDelta('3.00','2.00'),{amount:'-1.00',percentage:'-33.33'});
assert.deepEqual(decisionDelta('0.00','50.01'),{amount:'50.01',percentage:null});
assert.deepEqual(decisionDelta('-100.00','-150.00'),{amount:'-50.00',percentage:'-50.00'});
assert.deepEqual(decisionDelta('100000000000000.01','100000000000000.02'),{amount:'0.01',percentage:'0.00'});
assert.deepEqual(decisionDelta('0.32','0.33'),{amount:'0.01',percentage:'3.13'});
assert.deepEqual(decisionDelta('50.00','50.00'),{amount:'0.00',percentage:'0.00'});
for(const value of [null,undefined,'NaN','1e3','0.001','+5.00'])assert.throws(()=>decisionDelta(value,'1.00'));
console.log('PASS exact delta/percentage display, HALF_UP ties, negative/zero baselines and large cents');
