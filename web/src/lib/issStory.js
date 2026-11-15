// ISS 2006 story: the Elektron oxygen-generator leak of 18 September 2006, in the same shape as lib/mirStory.js
// (sources, briefing, five stages, debrief) plus its intro slides. Sources checked 2026-11-15: NASA's Mission
// Control status report of that day, and same-day Space.com and Associated Press reporting that quotes NASA's
// station program manager and the crew. Choices and text are original paraphrases; no quote is invented.
// Where the accounts disagree (smoke or no smoke, which liquid, first or second emergency), the debrief says so.
const ISS_STORY = {
  sources: {
    mcc: {title:'NASA · Mission Control status report',url:'https://mail.amsat.org/archives/pipermail/sarex/2006/000217.html',note:'STS-115 MCC Status Report #19, September 18, 2006, 1 p.m. CDT (archived copy). Overheating, odor, manual fire alarm, fans, masks, goggles and gloves.'},
    spacecom: {title:'Space.com · same-day report',url:'https://www.sliceofscifi.com/2006/09/18/space-station-crew-detects-smoke-like-smell-in-russian-segment/',note:'Tariq Malik, September 18, 2006 (republished). NASA program manager on the emergency declaration, ventilation and KOH; crew on the odor; timeline.'},
    ap: {title:'Associated Press · same-day report',url:'https://www.idsnews.com/article/2006/09/harmful-chemical-leaked-on-space-station',note:'September 18, 2006 (republished). Timeline, protective gear, charcoal filter, clean-up, and the crew’s descriptions.'},
    june: {title:'NASA status report · June 2006',url:'https://nasawatch.com/iss-news/elektron-offline-again/',note:'NASA ISS On-Orbit Status, June 8, 2006, as quoted by NASA Watch. An earlier Elektron shutdown and the backup oxygen.'}
  },
  briefing: 'Three people live aboard: commander Pavel Vinogradov, NASA’s Jeff Williams and ESA’s Thomas Reiter. In the Zvezda module, the Elektron machine makes oxygen from water. It was switched off while a shuttle was docked, and this morning it is switched back on.',
  stages: [
    {id:'alarm',label:'Raise the alarm',title:'A burning smell in Zvezda.',body:'Minutes after restart, the Elektron is hot and a bad smell spreads. The station’s fans keep the air moving between modules. What is the first move?',scene:'odor',source:'mcc',
      choices:[
        {label:'Keep working: a smell is not a fire.',good:false,effect:'spread',result:'In this imagined branch, nobody raises the alarm. The fans keep carrying whatever is in the air into the other modules.'},
        {label:'Trigger the fire alarm by hand, so the fans shut down.',good:true,effect:'alarm',result:'The alarm starts the emergency procedure and its software stops the ventilation fans. Your choice follows the documented response.'},
        {label:'Turn the fans up to blow the smell away.',good:false,effect:'spread',result:'In this imagined branch, stronger airflow dilutes the smell but spreads the source of it through the whole station. There is no window to open.'}
      ],record:'Vinogradov noticed the Elektron overheating, light smoke and a bad odor. The crew manually started a fire alarm, which let the software shut down the ventilation fans.',lesson:'In a sealed station, stopping the air from moving can be the first protective step.'},
    {id:'protect',label:'Protect the crew',title:'A clear liquid is leaking.',body:'Droplets of a clear liquid float near the Elektron. The machine uses potassium hydroxide (KOH), a chemical that irritates skin, eyes and lungs. How does the crew get close safely?',scene:'leak',source:'mcc',
      choices:[
        {label:'Wipe it up quickly with bare hands.',good:false,effect:'skin',result:'In this imagined branch, the liquid touches skin. KOH is corrosive: an irritant is still a hazard even when it is not a fire.'},
        {label:'Put on gloves, goggles and surgical masks first.',good:true,effect:'gear',result:'Protection matched to the hazard: skin, eyes and breathing. Your choice follows the documented response.'},
        {label:'Ignore it: KOH has no smell, so it cannot be the problem.',good:false,effect:'drift',result:'In this imagined branch, the crew rules out a hazard because of one clue. The smell and the liquid can have different sources and still both matter.'}
      ],record:'Mission Control asked the crew to briefly put on surgical masks, goggles and gloves against possible irritation from potassium hydroxide. They did not need their emergency gas masks.',lesson:'Match the protection to the hazard: here, skin and eyes as much as breathing.'},
    {id:'source',label:'Stop the source',title:'The station needs oxygen. The machine is leaking.',body:'The Elektron is one of the station’s oxygen supplies. It is overheating and leaking. What do you do with it?',scene:'source',source:'spacecom',
      choices:[
        {label:'Keep it running: oxygen comes first.',good:false,effect:'hot',result:'In this imagined branch, the leak and the heat continue. A damaged machine is not a reliable oxygen supply.'},
        {label:'Shut it down, then contain and bag the spill.',good:true,effect:'off',result:'The source stops, and the spill is collected and sealed. Your choice follows the documented response.'},
        {label:'Restart it to see whether it happens again.',good:false,effect:'hot',result:'In this imagined branch, the test repeats the hazard with the crew next to it. Diagnosis can wait until the machine is safe.'}
      ],record:'The Elektron was shut down at about 7:02 a.m. EDT. The crew cleaned up the liquid with towels and sealed them in two rubber bags.',lesson:'Stop the source first; work out the cause later.'},
    {id:'ground',label:'Call the ground',title:'Houston and Moscow are watching.',body:'Flight controllers can declare a “spacecraft emergency”. What should that declaration do here?',scene:'link',source:'spacecom',
      choices:[
        {label:'Order everyone into the Soyuz lifeboat now.',good:false,effect:'evacuate',result:'In this imagined branch, the crew abandons a station whose problem is already contained. Leaving has its own risks.'},
        {label:'Get priority on the relay satellites while the problem is worked.',good:true,effect:'priority',result:'The emergency gives the ground first call on communications, so the crew and controllers can talk without gaps. Your choice follows the record.'},
        {label:'Wait: report it once it is fixed.',good:false,effect:'silent',result:'In this imagined branch, the crew works alone while experts on the ground stay unaware. The two control centers have data and specialists the crew does not.'}
      ],record:'NASA and Russian managers declared a spacecraft emergency to gain access to communications satellites during the short crisis. NASA’s program manager said the chemical was not a life-threatening material.',lesson:'An emergency declaration can be about communication, not evacuation.'},
    {id:'air',label:'Clean the air',title:'The smell is fading. Is the air safe?',body:'With the fans off, the odor stays in Zvezda. Which plan brings the station back to normal?',scene:'air',source:'ap',
      choices:[
        {label:'The smell is gone, so the air is clean.',good:false,effect:'unchecked',result:'In this imagined branch, a nose replaces a measurement. Some hazards have no smell at all, KOH included.'},
        {label:'Scrub the air with a charcoal filter, check it, then restart the fans.',good:true,effect:'scrub',result:'The air is cleaned where the problem is, checked, and only then mixed again with the rest of the station. Your choice follows the record.'},
        {label:'Restart all fans at once to dilute it.',good:false,effect:'spread',result:'In this imagined branch, the remaining contamination is spread into every module before anyone knows what it is.'}
      ],record:'The crew ran a charcoal air-cleaning device and Williams reported the odor “decreased significantly.” Ventilation was restarted from the ground; by 9:05 a.m. EDT the smell had dwindled.',lesson:'Clean and check the air before you share it with the rest of the station.'}
  ],
  debrief:[
    {title:'The historical outcome',text:'NASA said the crew was doing well. They shut the Elektron down, cleaned up the spill and scrubbed the air within hours. Station officials estimated about 36 hours to fully exchange and scrub the station’s atmosphere.',source:'spacecom'},
    {title:'Smoke, or no smoke?',text:'Mission Control’s report says Vinogradov saw light smoke. Later the same day, Williams said there was never any smoke, and Vinogradov and controllers pointed to an overheated rubber seal as the source of the smell. We show a haze and a smell, not flames.',source:'spacecom'},
    {title:'Which liquid?',text:'NASA said potassium hydroxide “may have leaked”. Vinogradov described the liquid as clear, “like distilled water”. KOH itself has no smell, so the odor and the liquid may have had different sources.',source:'mcc'},
    {title:'First, or second emergency?',text:'The Associated Press called it the second spacecraft emergency in the station’s history, after an earlier false ammonia alarm. Some later accounts call it the first. We keep both rather than choose.',source:'ap'},
    {title:'Not the first Elektron trouble',text:'The Elektron had already shut down unexpectedly in June 2006. NASA noted then that oxygen could still come from tanks on Progress cargo ships: the Elektron is not the station’s only supply, which is why switching it off is a safe choice.',source:'june'}
  ],
  // The intro "video": NASA public-domain photos with their own NASA captions (images.nasa.gov).
  slides: [
    { id: "0700860", kicker: "Earth orbit · September 17, 2006",
      text: "The International Space Station, photographed from Space Shuttle Atlantis just after it undocked. The next morning, something goes wrong inside.",
      credit: "NASA · STS-115, September 17, 2006" },
    { id: "iss013e79160", kicker: "The people",
      text: "Expedition 13: NASA astronaut Jeff Williams, ESA astronaut Thomas Reiter and commander Pavel Vinogradov of Russia, nine days before the incident.",
      credit: "NASA · Expedition 13 crew in the Destiny laboratory, September 9, 2006" },
    { id: "iss013e27377", kicker: "Zvezda",
      text: "Zvezda, the Russian service module, is where the crew eats and sleeps, and where much of the life-support equipment runs. Here Vinogradov reads a procedures checklist.",
      credit: "NASA · Vinogradov in Zvezda, May 2006" },
    { id: "iss004e11792", kicker: "Air from water",
      text: "The Elektron makes oxygen for the cabin from water, using a potassium hydroxide solution. It was switched off while Atlantis was docked. (This photo shows it in 2002.)",
      credit: "NASA · an Expedition 4 astronaut working on the Elektron in Zvezda, April 2002" },
    { id: null, tone: "leak", kicker: "September 18, 2006 · early morning",
      text: "The Elektron is switched back on. Within half an hour, a strange smell reaches the crew. Now you guide the response.",
      credit: "" }
  ],
  facts: { url: "https://www.sliceofscifi.com/2006/09/18/space-station-crew-detects-smoke-like-smell-in-russian-segment/",
           label: "Facts: NASA status report and same-day reports, September 18, 2006" }
};

export default ISS_STORY;
