// Build master mic audio (16k mono) by concatenating project track-1 clips in order.
const fs = require('fs'), cp = require('child_process'), path = require('path');
const W = 'D:/EDIT VIDEO CLAUDE/VIEC-DANG-LAM/hermes-edit';
const PROJ = 'D:/EDIT VIDEO CLAUDE/VIEC-DANG-LAM/camtasia/huong-dan-chay-hermes-agent-vps-hostinger.tscproj';
const tl = JSON.parse(fs.readFileSync(W + '/timeline.json', 'utf8'));
fs.mkdirSync(W + '/audio_parts', { recursive: true });
let t = 0, segs = [], list = [];
tl.t1.forEach((c, i) => {
  if (c.scalar !== 1) console.log('scalar!=1', i, c.scalar);
  const src = PROJ + '/' + tl.bin[c.src];
  const out = `${W}/audio_parts/p${String(i).padStart(3, '0')}.wav`;
  if (!fs.existsSync(out)) {
    const r = cp.spawnSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(c.ms), '-t', String(c.dur), '-i', src, '-map', '0:a:0', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', out]);
    if (r.status !== 0) { console.log('fail', i, String(r.stderr)); process.exit(1); }
  }
  segs.push({ i, src: c.src, srcName: tl.bin[c.src], ms: c.ms, dur: c.dur, projStart: c.start, masterStart: +t.toFixed(3) });
  list.push(`file '${out}'`);
  t += c.dur;
});
fs.writeFileSync(W + '/audio_parts/list.txt', list.join('\n'));
fs.writeFileSync(W + '/segments.json', JSON.stringify(segs, null, 1));
const r = cp.spawnSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', W + '/audio_parts/list.txt', '-c', 'copy', W + '/master_16k.wav']);
console.log('master duration s', t.toFixed(1), 'status', r.status, String(r.stderr));
