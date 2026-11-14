// A small, safe markdown renderer for the assistant's answers: paragraphs, lists, tables,
// **bold**, `code` and [links](url). No raw HTML is ever inserted.
const SAFE_URL = /^(https?:\/\/|\/)/;

// onLink(url): called instead of opening links to an uploaded report's page ('/uploads/<id>/pages/<n>').
let onLinkHandler = null;

function link(text, url, key) {
  if (!SAFE_URL.test(url)) return text;
  if (url.startsWith("/uploads/") && onLinkHandler) {
    const h = onLinkHandler;
    return <a key={key} href={url} onClick={(e) => { e.preventDefault(); h(url); }}>{text}</a>;
  }
  return <a key={key} href={url} target="_blank" rel="noreferrer">{text}</a>;
}

function inline(text, key = 0) {
  const out = [];
  const re = /\[([^\]]+)\]\(([^)\s]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;
  let last = 0, m, i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1]) {
      out.push(link(m[1], m[2], `${key}-${i++}`));
    } else if (m[3]) out.push(<b key={`${key}-${i++}`}>{m[3]}</b>);
    else out.push(<code key={`${key}-${i++}`} className="mono">{m[4]}</code>);
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

const cells = (line) => line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

export default function Markdown({ text, onLink }) {
  onLinkHandler = onLink || null; // rendering is synchronous, so the handler is set for this render only
  const lines = text.split("\n");
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*([-*]|\d+\.)\s+/, ""));
        i++;
      }
      blocks.push(<ul key={i}>{items.map((t, j) => <li key={j}>{inline(t, j)}</li>)}</ul>);
    } else if (line.trim().startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        if (!/^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[i])) rows.push(cells(lines[i])); // skip the |---| row
        i++;
      }
      blocks.push(
        <table key={i} className="mdt"><tbody>
          {rows.map((r, j) => <tr key={j}>{r.map((c, k) => (j === 0 ? <th key={k}>{inline(c, k)}</th> : <td key={k}>{inline(c, k)}</td>))}</tr>)}
        </tbody></table>);
    } else {
      const para = [];
      while (i < lines.length && lines[i].trim() && !/^\s*([-*]|\d+\.)\s+/.test(lines[i]) && !lines[i].trim().startsWith("|")) {
        para.push(lines[i].replace(/^#+\s*/, ""));
        i++;
      }
      blocks.push(<p key={i}>{inline(para.join(" "), i)}</p>);
    }
  }
  return <>{blocks}</>;
}
