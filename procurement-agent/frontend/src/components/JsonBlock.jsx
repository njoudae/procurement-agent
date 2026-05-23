export default function JsonBlock({ value }) {
  let parsed = value;
  if (typeof value === "string") {
    try {
      parsed = JSON.parse(value);
    } catch {
      parsed = value;
    }
  }
  return <pre className="json-block">{typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2)}</pre>;
}
