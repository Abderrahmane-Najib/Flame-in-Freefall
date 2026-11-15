// Mir 1997 story: copied word for word from the team prototype (mir-1997-simulation/story.js, sources checked
// 2026-11-15, see its SOURCES.md). Only change: an ES module export instead of a window global.
/* Original paraphrases. Source IDs resolve in MIR_STORY.sources. */
const MIR_STORY = {
  sources: {
    history: {title:'NASA · Mir fire retrospective',url:'https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/',note:'John Uri, 2022. Crew, generator, teamwork, investigation and recovery.'},
    interview: {title:'NASA · Jerry Linenger’s account',url:'https://www.nasa.gov/history/SP-4225/documentation/mir-summaries/mir23/interviews.htm',note:'Mir-23 interview, March 21, 1997. Smoke, breathing devices and follow-up checks.'},
    report: {title:'NASA NESC · Mir case study',url:'https://ntrs.nasa.gov/api/citations/20210013869/downloads/20210013869.pdf',note:'NASA/TM–20210013869, §10.2.3. Equipment difficulties and fire response.'},
    review: {title:'NASA OIG · Shuttle–Mir review',url:'https://www.nasa.gov/history/SP-4225/documentation/admin-letter/letter.htm',note:'August 29, 1997, Fire Hazards section. Escape access, equipment and training.'},
    release: {title:'NASA · Original news release',url:'https://sma.nasa.gov/SignificantIncidents/assets/mir---the-fire---news-release.pdf',note:'February 24, 1997. Preliminary account; not the final investigation.'},
    esa: {title:'ESA · Ewald remembers the fire',url:'https://www.esa.int/articles/no-fire-in-the-sky-preventing-an-astronaut-s-worst-nightmare',note:'June 17, 2021. Crew perspective and later fire-safety research.'}
  },
  briefing: 'Six people are aboard during a crew handover. In Kvant-1, a solid-fuel oxygen generator supplements the station’s air supply. Then a canister erupts.',
  stages: [
    {id:'breathing',label:'Protect the crew',title:'Smoke fills the module.',body:'Visibility drops. The crew needs to act together. Which priority do you choose?',scene:'fire',source:'interview',
      choices:[
        {label:'Wait for the smoke to drift away.',good:false,effect:'smoke',result:'In this imagined branch, waiting leaves the crew exposed while visibility worsens. There is no outdoor air to step into.'},
        {label:'Use the emergency breathing equipment.',good:true,effect:'masks',result:'The crew gains breathing protection. Your choice follows the documented response.'},
        {label:'Focus on the flames; deal with breathing later.',good:false,effect:'smoke',result:'In this imagined branch, the crew prioritizes equipment over its own ability to function in smoke.'}
      ],record:'Linenger recalled rapidly spreading smoke and poor visibility. He changed breathing devices when the first was slow to activate; the crew used emergency breathing protection.',lesson:'Being able to breathe is part of being able to respond.'},
    {id:'teamwork',label:'Work as a team',title:'One firefighter needs a team.',body:'In a cramped, weightless cabin, reaching equipment and staying in position are challenges. Choose the crew’s approach.',scene:'masks',source:'history',
      choices:[
        {label:'Coordinate: stabilize the responder and pass extinguishers.',good:true,effect:'spray',result:'The crew works together. The scene now shows support and extinguisher use, rather than one person acting alone.'},
        {label:'Leave one person to handle everything.',good:false,effect:'alone',result:'In this imagined branch, one responder must handle position, access and equipment without help. The game pauses before returning to the record.'},
        {label:'Assume the first spray will instantly end the fire.',good:false,effect:'fire',result:'This branch assumes a guaranteed result that the evidence does not support. The fire did not vanish with one effortless action.'}
      ],record:'NASA’s retrospective describes Korzun using extinguishers while Linenger steadied him and others supplied more. The flame eventually died out; the response limited damage.',lesson:'Equipment access and teamwork matter alongside suppression.'},
    {id:'escape',label:'Understand the route',title:'Two capsules. One blocked route.',body:'The fire lies between the crew and one Soyuz. What does that mean for the evacuation plan?',scene:'route',source:'review',
      choices:[
        {label:'One reachable Soyuz can carry all six.',good:false,effect:'capacity',result:'In this hypothetical plan, the available capacity is insufficient. A reachable vehicle is not automatically an escape option for everyone.'},
        {label:'Two docked vehicles guarantee two usable exits.',good:false,effect:'blocked',result:'This hypothetical plan counts vehicles without considering access. The scene highlights the route interrupted by the fire.'},
        {label:'Recognize the access problem; reassess as a crew.',good:true,effect:'route',result:'Your assessment matches the documented hazard. A blocked route made evacuation more complicated; the actual crew remained aboard.'}
      ],record:'NASA’s 1997 review states that each Soyuz carried up to three people. All six were on one side of the fire, with access to only one vehicle.',lesson:'Redundancy depends on access, not just the number of backups.'},
    {id:'recovery',label:'Check the aftermath',title:'The flame is gone. Is it over?',body:'Smoke remains in the station. Choose what the crew should focus on next in this retelling.',scene:'aftermath',source:'interview',
      choices:[
        {label:'Declare the cabin safe because no flame is visible.',good:false,effect:'smoke',result:'This imagined branch confuses an extinguished flame with a safe atmosphere. The scene keeps the residual smoke visible.'},
        {label:'Continue recovery and monitor crew health.',good:true,effect:'recovery',result:'The focus shifts to the crew and the atmosphere. Recovery is represented as a later phase, not an instant reset.'}
      ],record:'Linenger described medical checks immediately after the incident and again at 24 and 48 hours. He reported no serious inhalation damage in his assessment.',lesson:'Fire response continues after visible burning stops.'},
    {id:'learning',label:'Learn from the incident',title:'What should change next?',body:'Back on Earth, engineers study the event. Choose the lesson you would carry into a future spacecraft.',scene:'recovery',source:'review',
      choices:[
        {label:'Survival proves that nothing needs to change.',good:false,effect:'review',result:'This hypothetical conclusion discards a chance to improve. A successful recovery does not erase equipment and preparation problems.'},
        {label:'Blame a crew member without evidence.',good:false,effect:'review',result:'This hypothetical conclusion jumps ahead of the investigation. An uncertain cause should not become a claim of individual fault.'},
        {label:'Improve access, hands-on preparation and communication.',good:true,effect:'complete',result:'You have reached the engineering lesson: make emergency systems easier to use together, under difficult conditions.'}
      ],record:'The NASA review called for accessible, clearly marked response equipment and thorough crew training and communication. It also identified conflicting accounts that needed resolution.',lesson:'An incident becomes useful evidence when it changes design and preparation.'}
  ],
  debrief:[
    {title:'The historical outcome',text:'The crew stayed aboard. NASA’s retrospective reports no structural damage or lasting harm; life support cleared smoke over several hours.',source:'history'},
    {title:'What started it?',text:'The damaged generator returned to Earth for study. NASA’s later account identifies accidentally introduced latex glove material as the most likely contaminant—not a proven act by a named person.',source:'history'},
    {title:'Why the controls are simplified',text:'The NESC case study describes breathing-device difficulties and Korzun changing from foam to water. This game does not simulate extinguisher chemistry, actual hardware operation, or a validated emergency procedure.',source:'report'},
    {title:'Why February, rather than an exact day?',text:'The 1997 NASA release and OIG account point to February 23; NASA’s 2022 retrospective uses February 24. The release gives about 90 seconds of burning, while later accounts describe minutes. We preserve these differences rather than invent a precise countdown.',source:'release'},
    {title:'A legacy beyond Mir',text:'ESA connects the crew’s experience with later ISS fire-safety procedures and research for future habitats. This is the bridge from a historical emergency to the questions Etna helps you explore.',source:'esa'}
  ]
};

// Increasing cognitive demand: recognize, coordinate, reason, assess, synthesize.
MIR_STORY.stages[2].body='Six people need an escape plan. Each Soyuz seats three, but fire blocks one route. Which conclusion follows?';
MIR_STORY.stages[3].body='The flame has stopped and visibility is improving. Which evidence is sufficient to declare recovery complete?';
MIR_STORY.stages[3].choices[0].label='Improved visibility alone proves the cabin is safe.';
MIR_STORY.stages[3].choices[1].label='Visibility alone is insufficient; continue atmospheric recovery and health checks.';
MIR_STORY.stages[3].choices.push({label:'A fixed waiting period is enough, without further checks.',good:false,effect:'smoke',result:'This imagined branch substitutes elapsed time for evidence. The haze remains while an arbitrary waiting rule leaves the actual conditions unassessed.'});
MIR_STORY.stages[4].body='You are reviewing the next mission. Which plan addresses equipment, crew readiness and uncertainty in the investigation together?';
MIR_STORY.stages[4].choices[0].label='Upgrade extinguishers; keep access and training unchanged.';
MIR_STORY.stages[4].choices[0].result='This hypothetical plan improves hardware but leaves access and practiced teamwork unresolved. The scene marks those remaining gaps.';
MIR_STORY.stages[4].choices[1].label='Repeat drills; keep equipment access unchanged and assume the cause is settled.';
MIR_STORY.stages[4].choices[1].result='This hypothetical plan improves practice but leaves equipment access and uncertainty unresolved. More rehearsal cannot settle an investigation.';
MIR_STORY.stages[4].choices[2].label='Improve access and hands-on drills; preserve uncertainty while investigating the cause.';

export default MIR_STORY;
