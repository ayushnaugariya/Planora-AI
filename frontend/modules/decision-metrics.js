// Display-only exact arithmetic over server Decimal strings; never updates a ledger.
export function decisionDelta(before,after){
  const cents=value=>{
    const text=String(value);if(!/^-?[0-9]+(?:\.[0-9]{1,2})?$/.test(text))throw Error('Invalid monetary display value');
    const negative=text.startsWith('-'),[whole,fraction='']=(negative?text.slice(1):text).split('.');
    return (BigInt(whole)*100n+BigInt(fraction.padEnd(2,'0')))*(negative?-1n:1n);
  };
  const base=cents(before),delta=cents(after)-base,abs=value=>value<0n?-value:value;
  const decimal=value=>`${value<0n?'-':''}${abs(value)/100n}.${String(abs(value)%100n).padStart(2,'0')}`;
  const denominator=abs(base),percentage=denominator===0n?null:decimal(((abs(delta)*10000n+denominator/2n)/denominator)*(delta<0n?-1n:1n));
  return {amount:decimal(delta),percentage};
}
