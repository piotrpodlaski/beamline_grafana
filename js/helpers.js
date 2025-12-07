// ---------- Helpers ----------
function getSeriesByRefId(data, refId) {
  if (!data || !data.series) return null;
  return data.series.find(s => s.refId === refId) || null;
}

function getSeriesByName(data, name) {
  if (!data || !data.series) return null;
  return data.series.find(s => s.name === name) || null;
};

function getLatestNumericFromSeries(series) {
  if (!series || !series.fields || series.fields.length === 0) return null;

  // Usually field[0] is time, field[1] is value
  let valueField = series.fields.find(f => f.type === 'number') || series.fields[1];
  if (!valueField || !valueField.values || valueField.values.length === 0) return null;

  const idx = valueField.values.length - 1;
  const raw =
    valueField.values.get
      ? valueField.values.get(idx)
      : valueField.values[idx];

  const num = Number(raw);
  return isNaN(num) ? null : num;
}

function mapValue(svgMap, svgField, pvName, unit, precision=1){
  if (!svgMap[svgField]) {
     console.log(`Field ${svgField} not found!`);
     return;
  }
  const series = getSeriesByName(data, pvName);

  if(!series) {
    svgMap[svgField].text(`NaN${unit}`);
    console.log(`Series ${pvName} not found!`);
    return;  
  }
  
  const raw = getLatestNumericFromSeries(series);
  svgMap[svgField].text(`${raw.toFixed(precision)}${unit}`);
}