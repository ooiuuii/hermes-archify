// Invoke only inside the supported browser Node session, passing its existing tab/CDP.
// The output is live Chromium screencast frames + their timestamps, not screenshots
// arranged to impersonate an interaction. No browser connection is created here.
import fs from 'node:fs/promises';

const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

export async function recordLive({tab, cdp, directory, durationMs, actions}) {
  await fs.mkdir(directory, {recursive:false});
  const frames = [], inputs = [];
  let cursor = (await cdp.readEvents({methods:['Page.screencastFrame']})).cursor;
  let running = true, started = 0, firstFrameResolve, pumpError;
  let pointer = {x:48, y:170};
  const firstFrame = new Promise(resolve => { firstFrameResolve = resolve; });
  await cdp.send('Input.dispatchMouseEvent', {type:'mouseMoved', ...pointer});
  await cdp.send('Page.startScreencast', {format:'jpeg', quality:94, everyNthFrame:2});
  const pump = (async () => {
    while (running) {
      const batch = await cdp.readEvents({afterSequence:cursor,
        methods:['Page.screencastFrame'], limit:100, timeoutMs:0});
      if (batch.truncated) throw Error('Screencast events were evicted; reject this recording');
      cursor = batch.cursor;
      for (const event of batch.events) {
        const p = event.params;
        await cdp.send('Page.screencastFrameAck', {sessionId:p.sessionId});
        const file = `${String(frames.length).padStart(6,'0')}.jpg`;
        await fs.writeFile(`${directory}/${file}`, Buffer.from(p.data, 'base64'));
        frames.push({file, timestamp:p.metadata.timestamp, metadata:p.metadata});
        if (!started) { started = Date.now(); firstFrameResolve(); }
      }
      // Long-polling this shared browser channel can delay input dispatch. Poll
      // without blocking the browser and yield locally between event batches.
      await pause(12);
    }
  })().catch(error => { pumpError = error; firstFrameResolve(); });
  const elapsed = () => Date.now() - started;
  const input = (type, detail) => inputs.push({ms:elapsed(), type, ...detail});
  const io = {
    at: async ms => { if (pumpError) throw pumpError; await pause(Math.max(0, ms-elapsed())); },
    move: async (target, ms=900) => {
      const from = {...pointer};
      const begin = Date.now(), steps = Math.max(2, Math.round(ms/40));
      for (let n=1; n<=steps; n++) {
        const u=n/steps, eased=u*u*(3-2*u);
        pointer={x:from.x+(target.x-from.x)*eased,y:from.y+(target.y-from.y)*eased};
        await cdp.send('Input.dispatchMouseEvent',{type:'mouseMoved',...pointer});
        input('mouseMoved', pointer);
        await pause(Math.max(0,begin+ms*n/steps-Date.now()));
      }
    },
    // Archify includes a hidden measurement copy with duplicate labels. Resolve the
    // observed label only among visible DOM elements, never guess a screen position.
    locate: async (role, name, index=0) => tab.playwright.evaluate(({name,index})=>{
      const targets=Array.from(document.querySelectorAll('[aria-label]'))
        .filter(el=>el.getAttribute('aria-label')===name)
        .map(el=>el.getBoundingClientRect())
        .filter(r=>r.width>0 && r.height>0 && r.top>=0 && r.bottom<=innerHeight && r.left>=0 && r.right<=innerWidth);
      const r=targets[index];
      if (!r) throw Error('Recording target must be fully visible: '+name);
      return {x:r.x+r.width/2,y:r.y+r.height/2};
    }, {name,index}),
    click: async () => {
      input('click',pointer);
      await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...pointer});
      await pause(85);
      await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...pointer});
    },
    type: async text => {
      for (const character of text) {
        await cdp.send('Input.insertText',{text:character});
        input('insertText',{text:character});
        await pause(105);
      }
    },
    snapshot: async name => {
      const snapshot=await tab.playwright.domSnapshot();
      await fs.writeFile(`${directory}/${name}.txt`,snapshot);
      input('domCheckpoint',{name});
      return snapshot;
    }
  };
  try {
    await Promise.race([firstFrame, pause(10000).then(()=>{throw Error('No screencast frame within 10 s');})]);
    if (pumpError) throw pumpError;
    await actions(io);
    await io.at(durationMs);
  } finally {
    const stopped=Date.now();
    await cdp.send('Page.stopScreencast');
    running=false;
    await pump;
    const first=frames[0]?.timestamp;
    const wallSeconds=started ? (stopped-started)/1000 : 0;
    const report={method:'Chromium Page.startScreencast, continuous live input',
      cursor:'Transient pointer overlay follows actual pointermove/pointerdown events',
      speed:1, wall_seconds:wallSeconds, frames, inputs,
      note:'Static intervals retain the last browser-emitted frame for their actual elapsed time. No synthetic transitions or post-hoc mouse animation.'};
    await fs.writeFile(`${directory}/capture.json`,JSON.stringify(report,null,2));
    if (!frames.length || pumpError) throw pumpError ?? Error('Empty screencast');
    const listing=['ffconcat version 1.0'];
    frames.forEach((frame,index)=>{
      const next=frames[index+1]?.timestamp ?? first+Math.max(wallSeconds,frame.timestamp-first+0.034);
      listing.push(`file '${frame.file}'`,'option framerate 1000',`duration ${Math.max(.001,next-frame.timestamp).toFixed(6)}`);
    });
    listing.push(`file '${frames.at(-1).file}'`,'option framerate 1000');
    await fs.writeFile(`${directory}/frames.ffconcat`,listing.join('\n')+'\n');
  }
  return {directory,frames:frames.length,seconds:(Date.now()-started)/1000,
    mouse_moves:inputs.filter(x=>x.type==='mouseMoved').length, clicks:inputs.filter(x=>x.type==='click').length};
}
