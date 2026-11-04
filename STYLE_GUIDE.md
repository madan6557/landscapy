# Landscapy — Shape-first stylized assets

This guide sets the visual order for every Landscapy generator. Forms should
read in a flat silhouette before texture, surface noise, or small accessories
are considered.

## Shape rules

- **Design the outer contour first.** Each preset needs a recognizable profile
  in a single dark material at a small on-screen size.
- **Build from meaningful masses.** Trees grow from trunk, primary limbs, and
  overlapping canopy groups. A tree canopy is branch-led; a bush or carpet is
  allowed to use free surface or volume scatter.
- **Inspect the bare wood at close range.** A branch should leave the trunk in
  a continuous curve with a broad collar that tapers into the limb. Check the
  joint with a neutral material and verify that both parts share one surface.
- **Keep large leaves large.** Banana-like blades extend from the crown as one
  continuous lamina. Palm-like foliage is a sweeping rachis with a restrained
  number of broad leaflet cards. Conifer foliage is a branch-sized card
  cluster placed on the primary whorls.
- **Use guided irregularity.** Seeds vary spacing, lean, droop, and size inside
  the species profile. They must not turn a recognizable form into unrelated
  noise or a repeated mechanical pattern.
- **Let anatomy explain the shape.** Roots leave the trunk as a few broad,
  tapering supports; mushrooms form a varied cluster with caps that keep their
  chosen profile; rocks use a few large planes and a broken, non-spherical
  contour.
- **Preserve shape across production steps.** High detail may add topology, but
  must not add distracting silhouette noise. Mid/Low/Flat builds should keep
  the outer form and meaningful negative spaces. Branch, cluster, and card
  anchors remain stable for attachment and wind.

## Research references

- Xun Zhang, *EvoVision*: the canopy envelope is modeled before three
  intersecting alpha cards are distributed with Geometry Nodes.
  [Production breakdown](https://xun.archi/ecovision)
- Rustam Zhukov, *Pines*: foliage detail is baked into a branch atlas,
  allowing each bough to read as a component at the tree scale.
  [Artist breakdown](https://rustamzhukov.artstation.com/projects/LRDkyr)

- Jane Ng, *The Art of Firewatch* (GDC): the spruce study describes a conical
  silhouette, upward-pointing upper branches, and drooping lower branches; the
  rock study calls for large planes and simple forms in negative space.
  [GDC slides](https://media.gdcvault.com/gdcchina15/slides/Ng_Jane_Art%20of%20Firewatch_EN.pdf)
- Gilbert Sanders and Guerrilla Games, *Between Tech and Art: The Vegetation
  of Horizon Zero Dawn* (GDC): the vegetation workflow builds component LODs
  and separates tree, branch, and leaf motion.
  [GDC slides](https://media.gdcvault.com/gdc2018/presentations/gilbert_sanders_between_tech_and.pdf)
- Epic Games, *Foliage Mode*: static-mesh foliage supports LODs and batches
  instances, which informs Landscapy's cluster-based game output.
  [Unreal Engine documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/foliage-mode-in-unreal-engine)
