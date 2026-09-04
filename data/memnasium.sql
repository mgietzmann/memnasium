BEGIN TRANSACTION;
CREATE TABLE draw (
    day            TEXT NOT NULL,       -- ISO date
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    PRIMARY KEY (day, recall_pair_id)
);
CREATE TABLE draw_day (
    day      TEXT PRIMARY KEY,   -- ISO date
    drawn    INTEGER NOT NULL,   -- how many pairs came out, for the day's record
    expected REAL NOT NULL       -- how many were expected to, computed at build
);
CREATE TABLE groups (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL           -- the matching key when placing a note
);
INSERT INTO "groups" VALUES(1,'Chinook salmon size and development','How big Chinook Salmon are at each stage and how fast they get there — smolt and juvenile size-at-age by region, growth rates and what drives them, and the sizes at which the switch to piscivory happens.');
INSERT INTO "groups" VALUES(2,'Juvenile Chinook salmon diet','What Chinook Salmon eat from ocean entry through their first summer at sea — Age-0 forage fish, invertebrates and insects, and how the mix shifts by region and season.');
INSERT INTO "groups" VALUES(3,'Immature and adult Chinook salmon diet','What Chinook Salmon eat once they are large enough to be reliably piscivorous — herring, sand lance, capelin and squid across inside, outside and offshore waters, ocean-age 2+ through the return migration.');
INSERT INTO "groups" VALUES(4,'Predators of Chinook salmon','Who eats Chinook Salmon and how much — the main predators by region (killer whales, pinnipeds, salmon sharks, birds, predatory fish including other Chinook) and the consumption and mortality estimates attached to them.');
INSERT INTO "groups" VALUES(5,'Chinook salmon marine survival','What kills Chinook Salmon at sea besides predators and what makes a year good or bad — early marine survival near the natal estuary, contaminants, size-selectivity, upwelling and El Niño, and the rangewide productivity decline.');
INSERT INTO "groups" VALUES(6,'Chinook salmon life cycle','The shape of a Chinook Salmon life from smolt to spawner — the ocean phases and how long they last, how far and how fast the migrations run, when the spawning run happens, and at what age fish mature.');
INSERT INTO "groups" VALUES(7,'Where Chinook salmon go and why','Why Chinook Salmon end up where they do — cold and deep tolerance versus other Pacific salmon, juveniles actively resisting transport to hold near productive water, and the currents and temperature cues that move them.');
INSERT INTO "groups" VALUES(8,'Chinook salmon evolution and lineage','Where Chinook Salmon came from and how their variation is organized — divergence times from the salmonid tree down to the modern lineages, and why life-history types like stream- and ocean-type are a continuum rather than discrete populations.');
INSERT INTO "groups" VALUES(9,'Chinook salmon stock composition','Whose fish are where — the mix of natal origins in any patch of ocean, how western Alaskan, Asian and Columbia stocks trade dominance by region and season, and how stocks are told apart.');
CREATE TABLE miss (
    id             INTEGER PRIMARY KEY,
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    day            TEXT NOT NULL,       -- ISO date
    user_answer    TEXT NOT NULL,       -- what was typed in the answer box
    user_source    TEXT NOT NULL        -- what was typed in the source box
);
CREATE TABLE note (
    id         INTEGER PRIMARY KEY,
    source_id  INTEGER NOT NULL REFERENCES source(id),
    statement  TEXT NOT NULL,           -- multi-line, may contain LaTeX
    created_on TEXT NOT NULL            -- ISO date
);
INSERT INTO "note" VALUES(1,1,'9 of 17 Evolutionarily Significant Units of Chinook Salmon are listed as endangered or threatened under the U.S. Endangered Species Act','2026-07-04');
INSERT INTO "note" VALUES(2,1,'Folks suggest that climatic cooling and the subsequent evolution of anadromy was a major catalyst for salmonid speciation','2026-07-04');
INSERT INTO "note" VALUES(3,1,'The genus Oncorhynchus diverged from Salvelinus in the late Oligocene, approximately 25 Ma. Chinook and Coho diverged from one another 9 Ma. ','2026-07-04');
INSERT INTO "note" VALUES(4,1,'The major genetic lineages of Chinook salmon are believed to have descended from a common ancestor between 50-100 ka. ','2026-07-04');
INSERT INTO "note" VALUES(5,1,'While there has been this idea of stream-type vs ocean-type salmon. This really only holds in the upper Columbia. Everywhere else the evidence is quite scant. ','2026-07-04');
INSERT INTO "note" VALUES(6,1,'Demonstrating parallelism at the DNA sequence level, it is now apparent that similar Chinook Salmon life-history types have evolved by way of different evolutionary pathways','2026-07-04');
INSERT INTO "note" VALUES(7,1,'In the northeast Pacific Ocean, Chinook Salmon Oncorhynchus tshawytscha populations range from central California (Sacramento River) north through Kotzebue Sound, Alaska and have been infrequently reported along the Arctic shores into Canada including the McKenzie River','2026-07-04');
INSERT INTO "note" VALUES(8,1,'There has been a general decline in Chinook salmon productivity over the recent decade starting about 2000','2026-07-04');
INSERT INTO "note" VALUES(9,1,'Chinook salmon near each other tend to have similar life history traits but there''s little in the way of unique populations - more like a steady and windy continuum. ','2026-07-04');
INSERT INTO "note" VALUES(10,1,'The history of artificial propagation of Chinook Salmon goes back 140 years beginning with the Baird Hatchery on the McCloud River, California.','2026-07-04');
INSERT INTO "note" VALUES(11,1,'Over the past decade, the aggregate releases of Chinook Salmon in the North Pacific has averaged 254 million per year.','2026-07-04');
INSERT INTO "note" VALUES(12,1,'Hatchery releases in Alaska are between 8 and 12 million Chinook salmon. In Canada it''s in the tens of millions. In CONUS its more like 200 million. ','2026-07-04');
INSERT INTO "note" VALUES(13,1,'A coded-wire tag is a piece of micro-wire (0.25 × 1.1 mm) that is etched with an identifying code and is injected into the snout of a fish. The wire is magnetized to enable detection of the wire.','2026-07-04');
INSERT INTO "note" VALUES(14,1,'The ocean life of Chinook Salmon along the eastern Pacific Rim can be portrayed as occurring in three general phases: 1) a juvenile seaward migration phase after smolting, spanning the first months of ocean life until winter, 2) an immature rearing phase in coastal and oceanic waters, lasting up to 5 years of ocean life, and 3) a final adult return migration phase to natal streams, spanning the last 4–10 months of ocean life.','2026-07-04');
INSERT INTO "note" VALUES(15,1,'A contributing factor to the complexity of ocean distribution of Chinook salmon is their association with colder temperatures (to 1°C) and deeper depths compared to the other species of Pacific salmon','2026-07-04');
INSERT INTO "note" VALUES(16,1,'Chinook Salmon may migrate only 100 km but others have been observed 2,500 km northward and/or westward, and are often prevalent in the coastal waters around the rim of the Gulf of Alaska from Southeast Alaska to the Aleutian Islands chain. The return migration phase of maturing Chinook Salmon is often the most rapid, sometimes lasting only weeks.','2026-07-04');
INSERT INTO "note" VALUES(17,1,'It is noteworthy that extreme ocean migrations are often mirrored in stocks with extensive up-river adult spawning migrations, often to interior or headwater locations within large river system','2026-07-04');
INSERT INTO "note" VALUES(18,1,'sub-yearling Chinook juveniles remain in proximity to their natal river (migration ranges from 100 to 300 km) during their first summer and fall, then move northward during the winter and following spring.','2026-07-04');
INSERT INTO "note" VALUES(19,1,'The majority of Asian Chinook mature at ages 1.2, 1.3, or 1.4','2026-07-05');
INSERT INTO "note" VALUES(20,1,'Juvenile chinook in coastal asia stay aggregated in small groups and forage with Coho salmon. Once they move offshore they form dense aggregations. ','2026-07-05');
INSERT INTO "note" VALUES(21,1,'Asian Chinook migrate to the Pacific Ocean when temperatures drop to 7C','2026-07-05');
INSERT INTO "note" VALUES(22,1,'Russian stocks of Chinook salmon dominate the west pacific. But the west and central bering sea are dominated by Alaska origin Chinook salmon.','2026-07-05');
INSERT INTO "note" VALUES(23,1,'There are no principle differences in the diets of juvenile, immature, or mature Chinook salmon in russia. They all eat fish, squids and euphausiids. For squid they primarily eat species of the family Gonatidae. ','2026-07-05');
INSERT INTO "note" VALUES(24,1,'The commander islands and the north kurile islands are spawning areas for squids. ','2026-07-05');
INSERT INTO "note" VALUES(25,1,'Larger asian chinook mainly occur in the bottom and near bottom trawl catches where adult squid Berryteuthis magister, predominate in the Chinook diet','2026-07-05');
INSERT INTO "note" VALUES(26,1,'Results for the southwest Bering Sea in June–July showed an average infection rate of 49% (incidence of any lice on a fish) and an intensity or load of 2.1 lice per fish. In the northwest Pacific Ocean in June through August, the average infection rate was 92.8% with an average load of 7.0 lice per fish','2026-07-05');
INSERT INTO "note" VALUES(27,1,'scale pattern analyses can differentiate Chinook from eastern and western Kamchatka with 94–95% accuracy.','2026-07-05');
INSERT INTO "note" VALUES(28,1,'Chinook Salmon smolts migrate into the eastern Bering Sea primarily from three large river drainages in western Alaska: the Yukon, Kuskokwim, and Nushagak rivers','2026-07-05');
INSERT INTO "note" VALUES(29,1,'the average run size of Chinook Salmon in the Yukon River is approximately 236,000 based on the average run of 118,000 Canadian-origin Chinook. The Kuskokwim River supports an average run of 259,000 Chinook Salmon and the Nushagak River supports an average run of 236,000 Chinook Salmon','2026-07-05');
INSERT INTO "note" VALUES(30,1,'Chinook Salmon production tends to reflect the amount of suitable spawning and rearing habitats, not river size.','2026-07-05');
INSERT INTO "note" VALUES(31,1,'Chinook Salmon in the Yukon River potentially undergo the longest salmon migration in the world up to 3,200 km including passing the Whitehorse Rapids dam','2026-07-05');
INSERT INTO "note" VALUES(32,1,'Chinook Salmon from Western Alaska begin their up-river spawning migration shortly after river ice break-up in the spring, typically late May, and peak migration generally occurs in June. Spawning migration (run timing) tends to occur slightly earlier in the Nushagak and Kuskokwim rivers than the Yukon River. Entry of Chinook Salmon into the Yukon River is stock structured, with stocks from the upper drainage arriving earlier than stocks from the lower drainage','2026-07-05');
INSERT INTO "note" VALUES(33,1,'Migration rates of Chinook Salmon are generally slower in the Kuskokwim and Nushagak rivers than the Yukon River. Chinook Salmon migration rates of 19–25 km/day are typical for the Kuskokwim River and 11–15 km/day are typical for the Nushagak River','2026-07-05');
INSERT INTO "note" VALUES(34,1,'Chinook Salmon reach the largest size and have the highest fecundity of all species of Pacific salmon. Egg size of Chinook Salmon is also relatively large and they have the largest emergent fry of Pacific salmon species','2026-07-05');
INSERT INTO "note" VALUES(35,1,'Western Alaska Chinook Salmon typically mature as age-1.2, 1.3 and 1.4, and females tend to mature later than males, characteristics that are consistent with other Chinook Salmon stocks in Alaska','2026-07-05');
INSERT INTO "note" VALUES(36,1,'Chinook Salmon from the Upper Yukon River tend to mature later than Nushagak and Kuskokwim River Chinook Salmon, which most likely reflects the higher energetic demand required to reach the upper Yukon River drainage.','2026-07-05');
INSERT INTO "note" VALUES(37,1,'Juvenile western alaskan Chinook begin to enter marine habitats in June and reach an average length of 87 mm fork length (FL) within Kuskokwim Bay. Juveniles grow rapidly during their initial marine period and approximately double in length within the first few months at sea reaching an average length of 190 mm to 220 mm FL, by about the end of August. Juvenile Chinook Salmon are distributed within shallow water (<50 m) habitats of the eastern Bering Sea shelf throughout most of their first summer at sea','2026-07-05');
INSERT INTO "note" VALUES(38,1,'Juveniles migrate against the northward flowing coastal currents to exit the northern Bering Sea shelf prior to the formation of winter sea ice. Juvenile Chinook Salmon tend to maintain a shallower distribution than Pink or Chum Salmon in the northern Bering Sea','2026-07-05');
INSERT INTO "note" VALUES(39,1,'Juvenile Chinook Salmon primarily feed on larval and juvenile stages of fish, predominately Capelin (Mallotus catevarius), Arctic Sandlance (Ammodytes hexapterus), Pacific Herring (Clupea pallasii), and Rainbow Smelt (Osmerus mordax). These prey species are primarily distributed in the shallow/nearshore habitats of the northern Bering Sea','2026-07-05');
INSERT INTO "note" VALUES(40,1,'Driftnet fishing for salmon and squid was closed in 1993 following the United Nations moratorium on driftnet fishing in international waters.','2026-07-06');
INSERT INTO "note" VALUES(41,1,'Unlike Chinook, other western alaskan salmon tend to rear in the Gulf of Alaska as opposed to the bering sea. ','2026-07-06');
INSERT INTO "note" VALUES(42,1,'Western Alaskan chinook account for around 80% of the driftnet fish catches in the Bering Sea vs 30% in the North Pacific. ','2026-07-06');
INSERT INTO "note" VALUES(43,1,'Western Alaskan Chinook contribute to the southern shelf highest in the winter and least in the summer. North pacific stocks were at their highest in summer and limited largely to the southern shelf. ','2026-07-06');
INSERT INTO "note" VALUES(44,1,'Yukon river chinook salmon tend to be distributed farther north than other western alaskan stocks of chinook salmon. ','2026-07-06');
INSERT INTO "note" VALUES(45,1,'The eastern Bering Sea cold pool is a persistent feature of the northern region of the eastern Bering Sea shelf that forms as a bi-product of winter sea ice','2026-07-06');
INSERT INTO "note" VALUES(46,1,'Western Alaska Chinook Salmon may utilize the northwest flowing currents along the eastern Bering Sea shelf break as a migratory corridor in the Bering Sea, particularly as age 1.1','2026-07-06');
INSERT INTO "note" VALUES(47,1,'Yukon River Chinook Salmon transition to piscivory in freshwater at approximately 85–90 mm. Approximately 90% of the diet of juvenile Chinook Salmon in the Yukon River delta consists of fish during their early seaward migration. Chinook Salmon remain predominately piscivorous throughout their first summer at sea from the onset of their marine residency in June','2026-07-06');
INSERT INTO "note" VALUES(48,1,'Capelin is the primary food source for juvenile Chinook in the northern bering sea whereas sand lance and walleye pollock are more important for southern eastern bering sea chinook (although sand lance is consistent in the diet of both regions). In all cases they are primarily feeding on Age-0 fish. ','2026-07-06');
INSERT INTO "note" VALUES(49,1,'The lack of Pacific Herring in the diet of juvenile Chinook Salmon may reflect the ability of Pacific Herring to outgrow the prey size window available to juvenile Chinook Salmon in the northern Bering Sea.','2026-07-06');
INSERT INTO "note" VALUES(50,1,'Invertebrate species are also an important component of juvenile Chinook Salmon diets in the northern Bering Sea, particularly within shallow habitats of Norton Sound. Invertebrate prey primarily consist of large invertebrate species such as crab megalops (Chinocetes sp.), and shrimp (Pandalus sp.); however species composition is variable and can include freshwater insects.','2026-07-06');
INSERT INTO "note" VALUES(51,1,'Immature Chinook Salmon predominately forage on fish and squid on the eastern Bering Sea shelf and in offshore habitats of the Bering Sea basin. Euphausiids also are an important prey species of Chinook Salmon in the Bering Sea basin','2026-07-06');
INSERT INTO "note" VALUES(52,1,'Squid were the largest component in the winter diet of Chinook Salmon. The combined contributions of Berrytheuthis magister and Gonatopsis borealis accounted for 74%–82% of the stomach content weight','2026-07-06');
INSERT INTO "note" VALUES(53,1,'Growth in juvenile Chinook salmon in the northern bering sea seems to peak in mid July ','2026-07-06');
INSERT INTO "note" VALUES(54,1,'Bioenergetic models indicate that temperature has significant effect on juvenile Chinook salmon growth rates','2026-07-06');
INSERT INTO "note" VALUES(55,1,'Although mortality during the juvenile life-history stage of Yukon River Chinook Salmon is size-selective, the average size of juveniles is not correlated with survival or adult returns','2026-07-07');
INSERT INTO "note" VALUES(56,1,'Tagging studies have suggested 40% salmon shark mortality of Chinook salmon in the Bering sea. ','2026-07-07');
INSERT INTO "note" VALUES(57,1,'When Ichthyophonus infections become clinical, parasite loads in muscle tissue and internal organs are visible to the naked eye, muscle tissue softens, and Chinook Salmon develop a distinctive odor','2026-07-07');
INSERT INTO "note" VALUES(58,1,'Chinook Salmon in the marine waters of southeast Alaskan (SEAK) archipelago and farther north and west along the coast of the Gulf of Alaska originate from hundreds of streams and rivers from Alaska south to California.','2026-07-07');
INSERT INTO "note" VALUES(59,1,'Diet studies for Chinook Salmon in SEAK support the characterization that Chinook are predominately piscivorous in coastal habitats. Primary prey species included Capelin, Sand Lance, and Pacific Herring; although a wide variety of other fishes and invertebrates were also observed.

Fish were also the primary prey for immature fish in SEAK marine waters, comprising 65% of the stomach contents by weight. Capelin were the predominant fish species, with Pacific Sand Lance, Pacific Herring, Lanternfishes, and Walleye Pollock secondary depending on sampling time.','2026-07-07');
INSERT INTO "note" VALUES(60,1,'more euphausiids were observed in juvenile SEAK Chinook Salmon in inlets, and euphausiids increased as a proportion of the diet of juvenile Chinook Salmon each month from June through September','2026-07-07');
INSERT INTO "note" VALUES(61,1,'Information on diets of larger immature and maturing Chinook Salmon (ocean-ages 2+) has been derived from samples from the commercial troll fishery in inside and outside waters of SEAK. Early studies showed that Pacific Herring was the most important prey species overall, comprising 60–68% of the stomach contents by volume, with Sand Lance the second most frequent prey. They get access to herring because of their larger size. ','2026-07-07');
INSERT INTO "note" VALUES(62,1,'Squid was more common in the diets of Chinook Salmon caught in more inside waters. Similarly, logbook records from SEAK commercial trollers have documented that Sand Lance and Pacific Herring are the major prey items observed in Chinook Salmon caught, with Pacific Herring predominating in fish taken in inside waters and Sand Lance predominating in fish taken in outside waters (this is all for age 2+ fish)','2026-07-07');
INSERT INTO "note" VALUES(63,1,'Chinook Salmon originating in SE Alaska rivers are predominately yearling smolts. Peak smolt outmigration occurs in early May and smolt sizes range from 54 to 120 mm, and average ~74 mm length and 4 gm. By late June, these 1.0+ Chinook sampled in SEAK marine waters (1997 to 2000) averaged 136 mm and 28 gm and 171 mm and 56 g, in inshore and strait habitats respectively. By September in these years, ocean-age zero Chinook Salmon averaged 210 mm and 114 g and 269 mm and 282 g in inshore and Icy Straits habitat respectively.','2026-07-07');
INSERT INTO "note" VALUES(64,1,'Wild stocks in SEAK on average had similar or higher marine survivals than hatchery stocks over the same time periods, even though wild smolts are substantially smaller at entry to the marine environment than hatchery smolts','2026-07-07');
INSERT INTO "note" VALUES(65,1,'by their second ocean summer SEAK Coho Salmon are three times larger than the same ocean-age SEAK Chinook Salmon.','2026-07-08');
INSERT INTO "note" VALUES(66,1,'Major large predators of SEAK Chinook salmon are resident killer whales, sea lions, and salmon sharks','2026-07-08');
INSERT INTO "note" VALUES(67,1,'During spring and summer, upper Columbia River yearling Chinook (spring runs) dominate catches of juvenile Chinook Salmon on the continental shelf, presumably because local stocks are still in the nearshore environment. by fall, Columbia River stocks have mostly been replaced by local stocks, which then continue to dominate catches throughout the winter','2026-07-08');
INSERT INTO "note" VALUES(68,1,'Relatively few juvenile Salish Sea Chinook Salmon are caught on the continental shelf off British Columbia until their first winter at sea, suggesting that they reside in the Strait of Georgia and Puget Sound for an extended period of time','2026-07-08');
INSERT INTO "note" VALUES(69,1,'In British Columbia Upon ocean entry, juvenile Chinook Salmon feed on a mixture of zooplankton and insects, feeding primarily on decapods, euphausiids, and hyperiid amphipods during summer','2026-07-08');
INSERT INTO "note" VALUES(70,1,'In british columbia Chinook salmon become primarily piscivorous around 50–100 g or 160–200 mm','2026-07-08');
INSERT INTO "note" VALUES(71,1,'The salmon louse is a common parasite frequently observed in wild and farmed salmonids. The prevalence of lice infection tends to be lower in coastal British Columbia compared to Alaska','2026-07-08');
INSERT INTO "note" VALUES(72,1,'There is consistently low survival in west coast vancouver island chinook salmon associated with el nino events. ','2026-07-08');
INSERT INTO "note" VALUES(73,1,'‘Salish Sea’ represents the combined areas from the western margin of the Strait of Juan de Fuca, all of Puget Sound, and north to Desolation Sound in the Strait of Georgia.','2026-07-08');
INSERT INTO "note" VALUES(74,1,'Salmon utilize estuaries for physiological acclimation, initial foraging in marine conditions, and for refuge from predators.','2026-07-08');
INSERT INTO "note" VALUES(75,1,' juvenile Chinook transiting contaminated estuaries in Puget sound had a 45% lower survival rate than Chinook that did not emigrate through contaminated sites. Contaminated here means contamination by industrial sites. ','2026-07-08');
INSERT INTO "note" VALUES(76,1,'Diets of Chinook salmon in estuaries with the smallest wetland losses included extensive feeding on mayflies, stoneflies, and caddis flies ... insects all associated with freshwater habitats.','2026-07-09');
INSERT INTO "note" VALUES(77,1,'In puget sound the onset of piscivory by habitat type is 70mm for inshore and 130mm for offshore','2026-07-09');
INSERT INTO "note" VALUES(78,1,'The pattern of early marine survival for Chinook salmon in the salish sea is largely determined by conditions in proximity to their source river/estuary, particularly for sub-yearlings.','2026-07-09');
INSERT INTO "note" VALUES(79,1,'Based on trawl surveys in the Salish sea it seems predation is not the primary mechanism that regulates salmon abundance during the early marine phase','2026-07-09');
INSERT INTO "note" VALUES(80,1,'Under one diet scenario, resident Chinook predation during June-August could impose 49–59% mortality on the annual cohort of juvenile Chinook entering Puget Sound. That''s a lot of cannibalism. ','2026-07-09');
INSERT INTO "note" VALUES(81,1,'In the Salish sea the primary marine mammal predators of Chinook salmon are harbor seals and killer whales. Currently, the Strait of Georgia has the highest density of Harbor Seals in the world.','2026-07-09');
INSERT INTO "note" VALUES(82,1,'There''s a “highly specialized and previously undocumented nocturnal foraging behaviour in which Harbor Seals congregated at night beneath two bridges that spanned the Puntledge River.” Their investigations determined that a small group of seals had learned this foraging behavior, but these seals were highly effective, consuming an estimated 14.5% of the Chum (averaging 140,000 chum fry per night) and 15% of the Coho Salmon (13,000 smolts per night) during their downstream migration','2026-07-09');
INSERT INTO "note" VALUES(83,1,'The predation of Chinook salmon by pinnepeds in the Salish sea is estimated to be equal to that by killer whales.','2026-07-09');
INSERT INTO "note" VALUES(84,1,'In the summer in the Salish sea Killer Whale diets are dominated by Chinook salmon (85% of salmon consumed). Chum salmon also get eaten regularly and they are also large, high lipid fish. ','2026-07-09');
INSERT INTO "note" VALUES(85,1,'While regional differences exist between the diets of juvenile Chinook Salmon from along the CCS, these differences are attributable to variability in the forage base and environmental conditions. ','2026-07-10');
INSERT INTO "note" VALUES(86,1,'Juvenile fish in the California current system start by eating invertebrates and then switch to piscivory later as they move offshore (where they eat juvenile rockfish and anchovy) ','2026-07-10');
INSERT INTO "note" VALUES(87,1,'Chinook Salmon juveniles may increase feeding intensity by using behaviors that maximize their interaction with prey such as following evolutionarily embedded navigational cues, tracking increasing gradients of prey resources, or residing at or near oceanographic fronts','2026-07-10');
INSERT INTO "note" VALUES(88,1,'The notion that CCS Chinook salmon use fronts is supported statistically significant relationship between salmon production and the probability of frontal development during the first few months at sea within the Gulf of the Farallones. Farther north in the Columbia River plume Chinook Salmon concentrate around salinity fronts, where prey was disproportionally more abundant in these frontal regions','2026-07-10');
INSERT INTO "note" VALUES(89,1,'Off Oregon and Washington, it has been demonstrated that Chinook Salmon juveniles behave in such a way as to reduce southerly transport or advection off shore, therefore, increasing the probability of remaining on a productive shelf to feed.','2026-07-10');
INSERT INTO "note" VALUES(90,1,'In more open waters of the northern California Current, squid represent a greater proportion of the adult salmon diet. As the fish return to their northern California Current natal region, in preparation to spawn, their diet is largely represented by California sardines (Sardinops caeruleus), Pacific Herring, Northern Anchovy, and euphausiids','2026-07-10');
INSERT INTO "note" VALUES(91,1,'The timing of upwelling in California can help or harm juvenile survival depending on whether enough time has transpired to setup the appropriate productivity. (Approximately 3 months) ','2026-07-10');
INSERT INTO "note" VALUES(92,1,'Along the California Current System (CCS), survivals of Chinook Salmon populations covary at a scale of approximately 700km; nearly the same spatial coherence of upwelling','2026-07-10');
INSERT INTO "note" VALUES(93,1,'In the california current system, predators that may have the greatest impact include piscivorous birds in the estuary and at sea, predatory fish, and, to a degree, marine mammals.','2026-07-10');
CREATE TABLE placement (
    id          INTEGER PRIMARY KEY,
    note_id     INTEGER NOT NULL REFERENCES note(id),
    group_id    INTEGER REFERENCES groups(id),
    pairs_stale INTEGER NOT NULL DEFAULT 0,   -- 0/1; pairs need rewriting
    UNIQUE (note_id, group_id)
);
INSERT INTO "placement" VALUES(1,37,1,0);
INSERT INTO "placement" VALUES(2,47,1,0);
INSERT INTO "placement" VALUES(3,53,1,0);
INSERT INTO "placement" VALUES(4,54,1,0);
INSERT INTO "placement" VALUES(5,63,1,0);
INSERT INTO "placement" VALUES(6,70,1,0);
INSERT INTO "placement" VALUES(7,77,1,0);
INSERT INTO "placement" VALUES(8,86,1,0);
INSERT INTO "placement" VALUES(9,39,2,0);
INSERT INTO "placement" VALUES(10,48,2,0);
INSERT INTO "placement" VALUES(11,50,2,0);
INSERT INTO "placement" VALUES(12,60,2,0);
INSERT INTO "placement" VALUES(13,69,2,0);
INSERT INTO "placement" VALUES(14,76,2,0);
INSERT INTO "placement" VALUES(15,85,2,0);
INSERT INTO "placement" VALUES(16,23,2,0);
INSERT INTO "placement" VALUES(17,23,3,0);
INSERT INTO "placement" VALUES(18,25,3,0);
INSERT INTO "placement" VALUES(19,51,3,0);
INSERT INTO "placement" VALUES(20,52,3,0);
INSERT INTO "placement" VALUES(21,59,3,0);
INSERT INTO "placement" VALUES(22,61,3,0);
INSERT INTO "placement" VALUES(23,62,3,0);
INSERT INTO "placement" VALUES(24,90,3,0);
INSERT INTO "placement" VALUES(25,56,4,0);
INSERT INTO "placement" VALUES(26,66,4,0);
INSERT INTO "placement" VALUES(27,80,4,0);
INSERT INTO "placement" VALUES(28,81,4,0);
INSERT INTO "placement" VALUES(29,82,4,0);
INSERT INTO "placement" VALUES(30,83,4,0);
INSERT INTO "placement" VALUES(31,84,4,0);
INSERT INTO "placement" VALUES(32,93,4,0);
INSERT INTO "placement" VALUES(33,80,3,0);
INSERT INTO "placement" VALUES(34,8,5,0);
INSERT INTO "placement" VALUES(35,55,5,0);
INSERT INTO "placement" VALUES(36,64,5,0);
INSERT INTO "placement" VALUES(37,72,5,0);
INSERT INTO "placement" VALUES(38,75,5,0);
INSERT INTO "placement" VALUES(39,78,5,0);
INSERT INTO "placement" VALUES(40,79,5,0);
INSERT INTO "placement" VALUES(41,91,5,0);
INSERT INTO "placement" VALUES(42,92,5,0);
INSERT INTO "placement" VALUES(43,14,6,0);
INSERT INTO "placement" VALUES(44,16,6,0);
INSERT INTO "placement" VALUES(45,17,6,0);
INSERT INTO "placement" VALUES(46,19,6,0);
INSERT INTO "placement" VALUES(47,31,6,0);
INSERT INTO "placement" VALUES(48,32,6,0);
INSERT INTO "placement" VALUES(49,33,6,0);
INSERT INTO "placement" VALUES(50,35,6,0);
INSERT INTO "placement" VALUES(51,36,6,0);
INSERT INTO "placement" VALUES(52,15,7,0);
INSERT INTO "placement" VALUES(53,18,7,0);
INSERT INTO "placement" VALUES(54,21,7,0);
INSERT INTO "placement" VALUES(55,38,7,0);
INSERT INTO "placement" VALUES(56,41,7,0);
INSERT INTO "placement" VALUES(57,46,7,0);
INSERT INTO "placement" VALUES(58,68,7,0);
INSERT INTO "placement" VALUES(59,89,7,0);
INSERT INTO "placement" VALUES(60,2,8,0);
INSERT INTO "placement" VALUES(61,3,8,0);
INSERT INTO "placement" VALUES(62,4,8,0);
INSERT INTO "placement" VALUES(63,5,8,0);
INSERT INTO "placement" VALUES(64,6,8,0);
INSERT INTO "placement" VALUES(65,9,8,0);
INSERT INTO "placement" VALUES(66,22,9,0);
INSERT INTO "placement" VALUES(67,27,9,0);
INSERT INTO "placement" VALUES(68,42,9,0);
INSERT INTO "placement" VALUES(69,43,9,0);
INSERT INTO "placement" VALUES(70,44,9,0);
INSERT INTO "placement" VALUES(71,58,9,0);
INSERT INTO "placement" VALUES(72,67,9,0);
INSERT INTO "placement" VALUES(73,1,NULL,0);
INSERT INTO "placement" VALUES(74,7,NULL,0);
INSERT INTO "placement" VALUES(75,10,NULL,0);
INSERT INTO "placement" VALUES(76,11,NULL,0);
INSERT INTO "placement" VALUES(77,12,NULL,0);
INSERT INTO "placement" VALUES(78,13,NULL,0);
INSERT INTO "placement" VALUES(79,20,NULL,0);
INSERT INTO "placement" VALUES(80,24,NULL,0);
INSERT INTO "placement" VALUES(81,26,NULL,0);
INSERT INTO "placement" VALUES(82,28,NULL,0);
INSERT INTO "placement" VALUES(83,29,NULL,0);
INSERT INTO "placement" VALUES(84,30,NULL,0);
INSERT INTO "placement" VALUES(85,34,NULL,0);
INSERT INTO "placement" VALUES(86,40,NULL,0);
INSERT INTO "placement" VALUES(87,45,NULL,0);
INSERT INTO "placement" VALUES(88,49,NULL,0);
INSERT INTO "placement" VALUES(89,57,NULL,0);
INSERT INTO "placement" VALUES(90,65,NULL,0);
INSERT INTO "placement" VALUES(91,71,NULL,0);
INSERT INTO "placement" VALUES(92,73,NULL,0);
INSERT INTO "placement" VALUES(93,74,NULL,0);
INSERT INTO "placement" VALUES(94,87,NULL,0);
INSERT INTO "placement" VALUES(95,88,NULL,0);
CREATE TABLE recall_pair (
    id               INTEGER PRIMARY KEY,
    placement_id     INTEGER NOT NULL REFERENCES placement(id),
    question         TEXT NOT NULL,
    answer           TEXT NOT NULL,
    sessions_correct INTEGER NOT NULL DEFAULT 0,
    retired          INTEGER NOT NULL DEFAULT 0    -- 0/1; no longer drilled or shown
);
INSERT INTO "recall_pair" VALUES(1,1,'Juvenile western Alaskan Chinook enter Kuskokwim Bay in June at what average FL?','87 mm',0,0);
INSERT INTO "recall_pair" VALUES(2,1,'Juvenile western Alaskan Chinook reach what average FL by end of August, first summer at sea?','190–220 mm',0,0);
INSERT INTO "recall_pair" VALUES(3,1,'Juvenile Chinook hold what depth on the eastern Bering Sea shelf their first summer?','Shallow water, <50 m',0,0);
INSERT INTO "recall_pair" VALUES(4,2,'Yukon River Chinook become piscivorous at what length in what water?','85–90 mm, in freshwater',0,0);
INSERT INTO "recall_pair" VALUES(5,2,'Fish make up what share of juvenile Chinook diet in the Yukon delta during seaward migration?','~90%',0,0);
INSERT INTO "recall_pair" VALUES(6,2,'Yukon River Chinook eat what through their first summer of marine residency?','Predominantly fish — piscivory holds from June on',0,0);
INSERT INTO "recall_pair" VALUES(7,3,'Juvenile Chinook growth in the northern Bering Sea peaks when?','Mid-July',0,0);
INSERT INTO "recall_pair" VALUES(8,4,'Bioenergetic models flag what as a significant effect on juvenile Chinook growth rates?','Temperature',0,0);
INSERT INTO "recall_pair" VALUES(9,5,'SE Alaska rivers produce predominantly what smolt type of Chinook?','Yearling smolts',0,0);
INSERT INTO "recall_pair" VALUES(10,5,'SEAK Chinook smolt outmigration peaks when?','Early May',0,0);
INSERT INTO "recall_pair" VALUES(11,5,'SEAK Chinook smolts leave at what size?','54–120 mm, averaging ~74 mm and 4 g',0,0);
INSERT INTO "recall_pair" VALUES(12,5,'Ocean-age-0 SEAK Chinook average what size by late June, inshore vs strait?','136 mm / 28 g inshore; 171 mm / 56 g strait',0,0);
INSERT INTO "recall_pair" VALUES(13,5,'Ocean-age-0 SEAK Chinook average what size by September, inshore vs Icy Strait?','210 mm / 114 g inshore; 269 mm / 282 g Icy Strait',0,0);
INSERT INTO "recall_pair" VALUES(14,6,'British Columbia Chinook become primarily piscivorous at what size?','50–100 g, or 160–200 mm',0,0);
INSERT INTO "recall_pair" VALUES(15,7,'Puget Sound Chinook begin piscivory at what length, inshore vs offshore?','70 mm inshore, 130 mm offshore',0,0);
INSERT INTO "recall_pair" VALUES(16,8,'California Current juvenile Chinook diet changes how as they move offshore?','Invertebrates first, then piscivory — juvenile rockfish and anchovy',0,0);
INSERT INTO "recall_pair" VALUES(17,9,'Juvenile Chinook feed primarily on what four fish species in the northern Bering Sea?','Capelin, Arctic sand lance, Pacific herring, rainbow smelt',0,0);
INSERT INTO "recall_pair" VALUES(18,9,'Juvenile Chinook''s fish prey sit in what northern Bering Sea habitat?','Shallow/nearshore',0,0);
INSERT INTO "recall_pair" VALUES(19,10,'Northern vs southern eastern Bering Sea juvenile Chinook take what primary prey?','Capelin north; sand lance and walleye pollock south — sand lance consistent in both',0,0);
INSERT INTO "recall_pair" VALUES(20,10,'Juvenile Chinook in the Bering Sea take fish of what age class?','Age-0',0,0);
INSERT INTO "recall_pair" VALUES(21,11,'Invertebrates matter most to juvenile Chinook in what northern Bering Sea location?','Shallow habitats of Norton Sound',0,0);
INSERT INTO "recall_pair" VALUES(22,11,'Juvenile Chinook invertebrate prey in the northern Bering Sea is mostly what?','Large inverts — crab megalops (Chionoecetes) and shrimp (Pandalus); variable, can include freshwater insects',0,0);
INSERT INTO "recall_pair" VALUES(23,12,'Euphausiids show up more in juvenile SEAK Chinook caught where?','Inlets',0,0);
INSERT INTO "recall_pair" VALUES(24,12,'Euphausiids in the juvenile SEAK Chinook diet trend how June through September?','Rising share every month',0,0);
INSERT INTO "recall_pair" VALUES(25,13,'BC juvenile Chinook eat what on ocean entry and through summer?','Zooplankton and insects — mainly decapods, euphausiids, hyperiid amphipods',0,0);
INSERT INTO "recall_pair" VALUES(26,14,'Chinook in estuaries with the smallest wetland losses fed extensively on what?','Freshwater insects — mayflies, stoneflies, caddisflies',0,0);
INSERT INTO "recall_pair" VALUES(27,15,'Regional diet differences in juvenile Chinook along the CCS come from what?','Variability in the forage base and environmental conditions',0,0);
INSERT INTO "recall_pair" VALUES(28,16,'Russian Chinook diets differ how across juvenile, immature, and mature?','They don''t — all eat fish, squid (mainly Gonatidae), and euphausiids',0,0);
INSERT INTO "recall_pair" VALUES(29,17,'Russian Chinook of all life stages eat what three things?','Fish, squid (mainly Gonatidae), euphausiids',0,0);
INSERT INTO "recall_pair" VALUES(30,18,'Larger Asian Chinook come up in bottom/near-bottom trawls eating mostly what?','Adult squid Berryteuthis magister',0,0);
INSERT INTO "recall_pair" VALUES(31,19,'Immature Chinook on the eastern Bering Sea shelf and basin forage predominantly on what?','Fish and squid',0,0);
INSERT INTO "recall_pair" VALUES(32,19,'Beyond fish and squid, what prey matters to Chinook in the Bering Sea basin?','Euphausiids',0,0);
INSERT INTO "recall_pair" VALUES(33,20,'The largest component of the Chinook winter diet is what?','Squid',0,0);
INSERT INTO "recall_pair" VALUES(34,20,'Berryteuthis magister and Gonatopsis borealis together make up what share of winter stomach content weight?','74–82%',0,0);
INSERT INTO "recall_pair" VALUES(35,21,'Chinook in SEAK coastal habitats take what three primary prey species?','Capelin, sand lance, Pacific herring',0,0);
INSERT INTO "recall_pair" VALUES(36,21,'Fish make up what share of immature Chinook stomach contents by weight in SEAK marine waters?','65%',0,0);
INSERT INTO "recall_pair" VALUES(37,21,'Capelin aside, what fish are secondary prey for immature SEAK Chinook?','Pacific sand lance, Pacific herring, lanternfishes, walleye pollock',0,0);
INSERT INTO "recall_pair" VALUES(38,22,'Troll-caught ocean-age-2+ Chinook in SEAK took what top prey, at what share?','Pacific herring, 60–68% of stomach contents by volume',0,0);
INSERT INTO "recall_pair" VALUES(39,22,'Second most frequent prey of ocean-age-2+ SEAK Chinook?','Sand lance',0,0);
INSERT INTO "recall_pair" VALUES(40,22,'Ocean-age-2+ Chinook get access to herring because of what?','Their larger size',0,0);
INSERT INTO "recall_pair" VALUES(41,23,'Herring vs sand lance dominate age-2+ SEAK Chinook in which waters?','Herring inside, sand lance outside',0,0);
INSERT INTO "recall_pair" VALUES(42,23,'Squid turns up more in SEAK Chinook caught in which waters?','Inside waters',0,0);
INSERT INTO "recall_pair" VALUES(43,24,'Squid makes up a bigger share of adult salmon diet in what part of the northern California Current?','The more open waters',0,0);
INSERT INTO "recall_pair" VALUES(44,24,'Returning northern California Current adults eat largely what before spawning?','California sardine, Pacific herring, northern anchovy, euphausiids',0,0);
INSERT INTO "recall_pair" VALUES(45,33,'Resident Chinook predation June–August could impose what mortality on the Puget Sound juvenile Chinook cohort?','49–59% — cannibalism',0,0);
INSERT INTO "recall_pair" VALUES(46,25,'Tagging studies put salmon shark mortality of Bering Sea Chinook at what rate?','40%',0,0);
INSERT INTO "recall_pair" VALUES(47,26,'SEAK Chinook have what three major large predators?','Resident killer whales, sea lions, salmon sharks',0,0);
INSERT INTO "recall_pair" VALUES(48,27,'Resident Chinook eating juveniles June–August could cost the Puget Sound cohort what mortality?','49–59%',0,0);
INSERT INTO "recall_pair" VALUES(49,28,'Salish Sea Chinook have what two primary marine mammal predators?','Harbor seals and killer whales',0,0);
INSERT INTO "recall_pair" VALUES(50,28,'The Strait of Georgia holds the world''s highest density of what?','Harbor seals',0,0);
INSERT INTO "recall_pair" VALUES(51,29,'Harbor seals on the Puntledge River learned what specialized foraging behavior?','Congregating at night beneath two bridges to take migrating smolts — previously undocumented nocturnal foraging',0,0);
INSERT INTO "recall_pair" VALUES(52,29,'The Puntledge River bridge seals took what share of the chum run, at what nightly rate?','14.5%, averaging 140,000 chum fry per night',0,0);
INSERT INTO "recall_pair" VALUES(53,29,'The Puntledge River bridge seals took what share of the coho run, at what nightly rate?','15%, about 13,000 smolts per night',0,0);
INSERT INTO "recall_pair" VALUES(54,30,'Pinniped predation on Salish Sea Chinook compares how to killer whale predation?','Estimated to be equal',0,0);
INSERT INTO "recall_pair" VALUES(55,31,'Chinook make up what share of salmon consumed by Salish Sea killer whales in summer?','85%',0,0);
INSERT INTO "recall_pair" VALUES(56,31,'Besides Chinook, Salish Sea killer whales regularly eat what salmon, and why?','Chum — also large and high-lipid',0,0);
INSERT INTO "recall_pair" VALUES(57,32,'California Current System predators with the greatest impact on Chinook are what?','Piscivorous birds in the estuary and at sea, predatory fish, and to a degree marine mammals',0,0);
INSERT INTO "recall_pair" VALUES(58,34,'Chinook salmon productivity has trended how, starting about when?','General decline, starting around 2000',0,0);
INSERT INTO "recall_pair" VALUES(59,35,'Juvenile mortality in Yukon River Chinook is size-selective, yet average juvenile size correlates with what?','Neither survival nor adult returns',0,0);
INSERT INTO "recall_pair" VALUES(60,36,'Wild vs hatchery SEAK stocks show what marine survival, despite what size difference?','Wild similar or higher, even though wild smolts enter substantially smaller',0,0);
INSERT INTO "recall_pair" VALUES(61,37,'West coast Vancouver Island Chinook survival is consistently low under what condition?','El Niño events',0,0);
INSERT INTO "recall_pair" VALUES(62,38,'Juvenile Chinook transiting industrially contaminated Puget Sound estuaries survive at what rate?','45% lower than those not emigrating through contaminated sites',0,0);
INSERT INTO "recall_pair" VALUES(63,39,'Early marine survival of Salish Sea Chinook is determined largely by what, and for which fish especially?','Conditions near their source river/estuary — especially sub-yearlings',0,0);
INSERT INTO "recall_pair" VALUES(64,40,'Salish Sea trawl surveys say what about predation as a regulator of early marine salmon abundance?','It isn''t the primary mechanism',0,0);
INSERT INTO "recall_pair" VALUES(65,41,'Upwelling timing in California helps or harms juvenile survival depending on what?','Whether enough time has passed to set up productivity — roughly 3 months',0,0);
INSERT INTO "recall_pair" VALUES(66,42,'Chinook survivals along the California Current System covary at what spatial scale, matching what?','~700 km — nearly the spatial coherence of upwelling',0,0);
INSERT INTO "recall_pair" VALUES(67,43,'Chinook ocean life along the eastern Pacific Rim breaks into what three phases?','Juvenile seaward migration after smolting; immature rearing in coastal and oceanic waters; adult return migration to natal streams',0,0);
INSERT INTO "recall_pair" VALUES(68,43,'The juvenile seaward migration phase of Chinook ocean life spans what period?','The first months of ocean life, until winter',0,0);
INSERT INTO "recall_pair" VALUES(69,43,'The immature rearing phase of Chinook ocean life lasts how long?','Up to 5 years of ocean life',0,0);
INSERT INTO "recall_pair" VALUES(70,43,'The adult return migration phase of Chinook ocean life spans what period?','The last 4–10 months of ocean life',0,0);
INSERT INTO "recall_pair" VALUES(71,44,'Chinook ocean migration distances range from what to what?','As little as 100 km up to 2,500 km north and/or west',0,0);
INSERT INTO "recall_pair" VALUES(72,44,'Chinook are often prevalent in what coastal waters?','Around the rim of the Gulf of Alaska, from SE Alaska to the Aleutian chain',0,0);
INSERT INTO "recall_pair" VALUES(73,44,'The return migration of maturing Chinook is notable for what?','It''s the most rapid phase — sometimes only weeks',0,0);
INSERT INTO "recall_pair" VALUES(74,45,'Extreme ocean migrations in Chinook tend to be mirrored by what?','Extensive up-river spawning migrations — to interior or headwater locations in large river systems',0,0);
INSERT INTO "recall_pair" VALUES(75,46,'Asian Chinook mature mostly at what ages?','1.2, 1.3, or 1.4',0,0);
INSERT INTO "recall_pair" VALUES(76,47,'Yukon River Chinook undertake a migration of what length, notable why?','Up to 3,200 km — potentially the longest salmon migration in the world',0,0);
INSERT INTO "recall_pair" VALUES(77,47,'Yukon River Chinook pass what dam on their migration?','The Whitehorse Rapids dam',0,0);
INSERT INTO "recall_pair" VALUES(78,48,'Western Alaska Chinook start their up-river spawning migration when?','Shortly after river ice break-up, typically late May, peaking in June',0,0);
INSERT INTO "recall_pair" VALUES(79,48,'Run timing in the Nushagak and Kuskokwim compares how to the Yukon?','Slightly earlier',0,0);
INSERT INTO "recall_pair" VALUES(80,48,'Yukon River Chinook entry is stock structured how?','Upper-drainage stocks arrive earlier than lower-drainage stocks',0,0);
INSERT INTO "recall_pair" VALUES(81,49,'Chinook migration rates in the Kuskokwim and Nushagak compare how to the Yukon?','Generally slower',0,0);
INSERT INTO "recall_pair" VALUES(82,49,'Typical Chinook migration rate in the Kuskokwim River?','19–25 km/day',0,0);
INSERT INTO "recall_pair" VALUES(83,49,'Typical Chinook migration rate in the Nushagak River?','11–15 km/day',0,0);
INSERT INTO "recall_pair" VALUES(84,50,'Western Alaska Chinook typically mature at what ages?','1.2, 1.3, 1.4',0,0);
INSERT INTO "recall_pair" VALUES(85,50,'Female vs male Chinook maturation timing in Alaska stocks runs how?','Females mature later than males',0,0);
INSERT INTO "recall_pair" VALUES(86,51,'Upper Yukon Chinook mature when relative to Nushagak and Kuskokwim fish, and why?','Later — the higher energetic demand of reaching the upper Yukon drainage',0,0);
INSERT INTO "recall_pair" VALUES(87,52,'Chinook associate with what temperatures and depths compared to other Pacific salmon?','Colder (to 1°C) and deeper',0,0);
INSERT INTO "recall_pair" VALUES(88,53,'Sub-yearling Chinook juveniles stay within what range of their natal river their first summer and fall?','100–300 km',0,0);
INSERT INTO "recall_pair" VALUES(89,53,'Sub-yearling Chinook juveniles move which way during winter and the following spring?','Northward',0,0);
INSERT INTO "recall_pair" VALUES(90,54,'Asian Chinook migrate out to the Pacific Ocean at what temperature?','When temperatures drop to 7°C',0,0);
INSERT INTO "recall_pair" VALUES(91,55,'Juvenile Chinook exit the northern Bering Sea shelf how, and before what?','Migrating against the northward coastal currents, before winter sea ice forms',0,0);
INSERT INTO "recall_pair" VALUES(92,55,'Juvenile Chinook sit at what depth relative to pink and chum in the northern Bering Sea?','Shallower',0,0);
INSERT INTO "recall_pair" VALUES(93,56,'Western Alaskan salmon other than Chinook rear where instead?','The Gulf of Alaska, rather than the Bering Sea',0,0);
INSERT INTO "recall_pair" VALUES(94,57,'Western Alaska Chinook may use what Bering Sea migratory corridor, at what age especially?','The northwest-flowing currents along the eastern Bering Sea shelf break — particularly age 1.1',0,0);
INSERT INTO "recall_pair" VALUES(95,58,'Few juvenile Salish Sea Chinook appear on the BC continental shelf until when, implying what?','Until their first winter at sea — they reside in the Strait of Georgia and Puget Sound for an extended period',0,0);
INSERT INTO "recall_pair" VALUES(96,59,'Juvenile Chinook off Oregon and Washington behave how, to what end?','They reduce southerly transport and offshore advection, staying on the productive shelf to feed',0,0);
INSERT INTO "recall_pair" VALUES(97,60,'What is suggested as a major catalyst for salmonid speciation?','Climatic cooling and the subsequent evolution of anadromy',0,0);
INSERT INTO "recall_pair" VALUES(98,61,'Oncorhynchus diverged from Salvelinus when?','Late Oligocene, ~25 Ma',0,0);
INSERT INTO "recall_pair" VALUES(99,61,'Chinook and coho diverged from each other when?','9 Ma',0,0);
INSERT INTO "recall_pair" VALUES(100,62,'The major genetic lineages of Chinook descend from a common ancestor how long ago?','50–100 ka',0,0);
INSERT INTO "recall_pair" VALUES(101,63,'The stream-type vs ocean-type Chinook distinction holds up where?','Really only the upper Columbia — elsewhere the evidence is scant',0,0);
INSERT INTO "recall_pair" VALUES(102,64,'DNA sequence evidence of parallelism in Chinook shows what about life-history types?','Similar life-history types evolved by different evolutionary pathways',0,0);
INSERT INTO "recall_pair" VALUES(103,65,'Chinook life history traits are structured how across geography?','Nearby fish resemble each other, but there are few unique populations — a steady, windy continuum',0,0);
INSERT INTO "recall_pair" VALUES(104,66,'Chinook of what origin dominate the west Pacific?','Russian stocks',0,0);
INSERT INTO "recall_pair" VALUES(105,66,'Chinook of what origin dominate the west and central Bering Sea?','Alaska-origin stocks',0,0);
INSERT INTO "recall_pair" VALUES(106,67,'Scale pattern analysis separates eastern from western Kamchatka Chinook at what accuracy?','94–95%',0,0);
INSERT INTO "recall_pair" VALUES(107,68,'Western Alaskan Chinook make up what share of Bering Sea driftnet catches?','~80%',0,0);
INSERT INTO "recall_pair" VALUES(108,68,'Western Alaskan Chinook make up what share of North Pacific driftnet catches?','~30%',0,0);
INSERT INTO "recall_pair" VALUES(109,69,'Western Alaskan Chinook contribute to the southern shelf most and least in what seasons?','Highest in winter, least in summer',0,0);
INSERT INTO "recall_pair" VALUES(110,69,'North Pacific stocks peak on the shelf when, and are confined where?','Highest in summer, largely limited to the southern shelf',0,0);
INSERT INTO "recall_pair" VALUES(111,70,'Yukon River Chinook distribute where relative to other western Alaskan stocks?','Farther north',0,0);
INSERT INTO "recall_pair" VALUES(112,71,'Chinook in SEAK and Gulf of Alaska coastal waters originate from where?','Hundreds of streams and rivers from Alaska south to California',0,0);
INSERT INTO "recall_pair" VALUES(113,72,'Juvenile Chinook catches on the continental shelf in spring and summer are dominated by what stock, and why?','Upper Columbia River yearling (spring-run) Chinook — local stocks are still nearshore',0,0);
INSERT INTO "recall_pair" VALUES(114,72,'Juvenile Chinook shelf catches shift to what stock by fall, holding through when?','Local stocks — dominant through the winter',0,0);
INSERT INTO "recall_pair" VALUES(115,73,'How many Chinook salmon Evolutionarily Significant Units are ESA-listed, out of how many?','9 of 17, endangered or threatened',0,0);
INSERT INTO "recall_pair" VALUES(116,74,'Chinook salmon populations in the northeast Pacific span what range?','Central California (Sacramento River) north through Kotzebue Sound, Alaska',0,0);
INSERT INTO "recall_pair" VALUES(117,74,'Chinook salmon have been infrequently reported in what waters beyond their usual range?','Along Arctic shores into Canada, including the McKenzie River',0,0);
INSERT INTO "recall_pair" VALUES(118,74,'The scientific name of Chinook salmon?','Oncorhynchus tshawytscha',0,0);
INSERT INTO "recall_pair" VALUES(119,75,'Artificial propagation of Chinook salmon began where and how long ago?','The Baird Hatchery on the McCloud River, California — 140 years ago',0,0);
INSERT INTO "recall_pair" VALUES(120,76,'Aggregate Chinook salmon releases in the North Pacific have averaged how many per year over the past decade?','254 million',0,0);
INSERT INTO "recall_pair" VALUES(121,77,'Alaska releases how many hatchery Chinook salmon?','8–12 million',0,0);
INSERT INTO "recall_pair" VALUES(122,77,'Canada releases how many hatchery Chinook salmon?','Tens of millions',0,0);
INSERT INTO "recall_pair" VALUES(123,77,'The continental US releases how many hatchery Chinook salmon?','~200 million',0,0);
INSERT INTO "recall_pair" VALUES(124,78,'A coded-wire tag is what, and goes where in a fish?','A 0.25 × 1.1 mm micro-wire etched with an identifying code, injected into the snout',0,0);
INSERT INTO "recall_pair" VALUES(125,78,'A coded-wire tag is magnetized why?','To enable detection of the wire',0,0);
INSERT INTO "recall_pair" VALUES(126,79,'Juvenile Chinook in coastal Asia aggregate how, and forage with what species?','In small groups, foraging with coho salmon',0,0);
INSERT INTO "recall_pair" VALUES(127,79,'Juvenile Chinook in Asia change their aggregation how once offshore?','They form dense aggregations',0,0);
INSERT INTO "recall_pair" VALUES(128,80,'What two island groups are squid spawning areas?','The Commander Islands and the north Kurile Islands',0,0);
INSERT INTO "recall_pair" VALUES(129,81,'Sea lice infection rate and load in the southwest Bering Sea, June–July?','49% infection rate, 2.1 lice per fish',0,0);
INSERT INTO "recall_pair" VALUES(130,81,'Sea lice infection rate and load in the northwest Pacific, June–August?','92.8% infection rate, 7.0 lice per fish',0,0);
INSERT INTO "recall_pair" VALUES(131,82,'Chinook smolts enter the eastern Bering Sea primarily from what three western Alaska drainages?','The Yukon, Kuskokwim, and Nushagak rivers',0,0);
INSERT INTO "recall_pair" VALUES(132,83,'Average Chinook run size in the Yukon River, and the Canadian-origin share?','~236,000 total; 118,000 Canadian-origin',0,0);
INSERT INTO "recall_pair" VALUES(133,83,'Average Chinook run size in the Kuskokwim River?','259,000',0,0);
INSERT INTO "recall_pair" VALUES(134,83,'Average Chinook run size in the Nushagak River?','236,000',0,0);
INSERT INTO "recall_pair" VALUES(135,84,'Chinook salmon production tracks what, rather than river size?','The amount of suitable spawning and rearing habitat',0,0);
INSERT INTO "recall_pair" VALUES(136,85,'Chinook rank where among Pacific salmon for size and fecundity?','Largest size and highest fecundity of all Pacific salmon',0,0);
INSERT INTO "recall_pair" VALUES(137,85,'Chinook egg size and emergent fry size rank where among Pacific salmon?','Relatively large eggs; the largest emergent fry',0,0);
INSERT INTO "recall_pair" VALUES(138,86,'Driftnet fishing for salmon and squid closed in what year, under what?','1993, under the UN moratorium on driftnet fishing in international waters',0,0);
INSERT INTO "recall_pair" VALUES(139,87,'The eastern Bering Sea cold pool sits where and forms from what?','The northern eastern Bering Sea shelf — a by-product of winter sea ice',0,0);
INSERT INTO "recall_pair" VALUES(140,88,'Pacific herring are scarce in northern Bering Sea juvenile Chinook diets possibly why?','Herring outgrow the prey size window available to juvenile Chinook',0,0);
INSERT INTO "recall_pair" VALUES(141,89,'Clinical Ichthyophonus infection in Chinook presents how?','Parasite loads visible to the naked eye in muscle and organs, softened muscle tissue, a distinctive odor',0,0);
INSERT INTO "recall_pair" VALUES(142,90,'SEAK coho compare in size to same ocean-age SEAK Chinook by their second ocean summer how?','Three times larger',0,0);
INSERT INTO "recall_pair" VALUES(143,91,'Salmon louse prevalence in coastal British Columbia compares how to Alaska?','Lower in coastal BC',0,0);
INSERT INTO "recall_pair" VALUES(144,92,'The ''Salish Sea'' covers what area?','The western margin of the Strait of Juan de Fuca, all of Puget Sound, north to Desolation Sound in the Strait of Georgia',0,0);
INSERT INTO "recall_pair" VALUES(145,93,'Salmon use estuaries for what three things?','Physiological acclimation, initial foraging in marine conditions, refuge from predators',0,0);
INSERT INTO "recall_pair" VALUES(146,94,'Juvenile Chinook may raise feeding intensity through what behaviors?','Following evolutionarily embedded navigational cues, tracking increasing prey gradients, residing at or near oceanographic fronts',0,0);
INSERT INTO "recall_pair" VALUES(147,95,'What statistical evidence supports CCS Chinook using fronts, and where?','A significant relationship between salmon production and probability of frontal development during the first months at sea, in the Gulf of the Farallones',0,0);
INSERT INTO "recall_pair" VALUES(148,95,'Chinook concentrate around what feature in the Columbia River plume, and why?','Salinity fronts — prey was disproportionately more abundant there',0,0);
CREATE TABLE source (
    id          INTEGER PRIMARY KEY,
    author      TEXT NOT NULL,          -- primary author
    year        INTEGER NOT NULL,
    publication TEXT                    -- book/paper title; optional
);
INSERT INTO "source" VALUES(1,'Riddell',2018,'Ocean Ecology of Chinook Salmon');
CREATE UNIQUE INDEX placement_roll ON placement (note_id) WHERE group_id IS NULL;
COMMIT;
