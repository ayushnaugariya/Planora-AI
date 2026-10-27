// Exact-cent display regression for the production formatter, without npm.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const source = readFileSync(new URL("../../frontend/modules/helpers.js", import.meta.url), "utf8");
const formatter = source.match(/  function financialMoney\(value[^)]*\) \{[\s\S]*?\n  \}/)?.[0];
assert(formatter, "Production money formatter not found");
const context = vm.createContext({ state: {workspace: { details: { currency: "USD" } } },
  Intl: { NumberFormat: class extends Intl.NumberFormat { constructor(_locale, options) { super("en-US", options); } } } });
vm.runInContext(formatter, context);
for (const [input, expected] of [
  ["100000000000000.01", "$100,000,000,000,000.01"],
  ["-100000000000000.01", "-$100,000,000,000,000.01"],
  ["-0.01", "-$0.01"], ["1234.50", "$1,234.50"], ["0", "$0.00"], [null, "Unknown"],
]) {
  context.input = input;
  assert.equal(vm.runInContext("financialMoney(input)", context), expected);
}
console.log("PASS exact-cent currency display, including large totals and negative fractions");
assert.equal(vm.runInContext('financialMoney("100000000000000.01", "INR")', context), '₹100,000,000,000,000.01');
