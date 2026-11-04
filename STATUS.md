# Status terhadap rencana Landscapy

## Landscapy 2.0 Architectural Plan & Directives (Library-Based Stylized Nature Toolkit)

### 1. Directives & Core Philosophy
- **Name & Goal**: **Landscapy** — A versatile, playful, and expressive stylized landscaping toolkit (NOT photorealistic).
- **Stylized Shading**: Solid/flat color palettes with smooth volumetric normal blending. Absolutely ZERO muddy photorealistic grain or noisy procedural bark textures.
- **Library-Based & Predictable (VRIKSH Inspiration, 100% Original Content)**:
  - We do NOT copy any third-party assets, meshes, or textures from VRIKSH or external packs.
  - All assets in `landscapy/assets/landscapy_library.blend` are 100% original, copyright-free, procedurally sculpted stylized components authored specifically for Landscapy.
  - Replaces unruly, unpredictable generative math ("susah ditebak dan dikendalikan") with art-directed, predictable, interactive curve trunks and modular foliage collections.
- **Original Landscapy Concept Fully Preserved**:
  - The entire existing hierarchy: `Plant Type` -> `Trunk Type` -> `Leaf Type` -> `Fruit Type` -> `Ornament Type`.
  - Full two-in-one generator: trunk and leaves can be generated together or separately.
  - Control mesh customization: Volumeless plane spawns carpet/grass; Curve/path guides; Manual individual spawning.
  - Ivy: Curve/path or plane controller.
  - Multi-texture RGBA slots with weights and full randomization (Hue, Saturation, Value, Size, Orientation/Rotation, Opacity).
  - Valley quad: 4-triangle quad with sunken center valley/peak for volume in low-poly flowers and foliage.
  - Wind animation: Real-time trunk sway, branch movement, leaf flutter, automatic ornament binding.
  - Hybrid Render & Game / Apply LODs: One-click export into 4 separate collections (`LOD_High`, `LOD_Mid`, `LOD_Low`, `LOD_Flat`), with batch apply for groups/collections.
  - Props & Obstacles: Faceted stylized rocks, hollow trunks, cut trunks/fallen logs, vines.
  - Mushrooms: Cap + gills + stem, clusters, tree oyster/shelf bracket mushrooms that snap to trunk, glowing mushrooms (under cap / whole / top cap only with custom color & intensity), auto-bending upwards with threshold.

### 2. Dual-Engine Architecture
1. **Engine A (Classic Procedural & Mesh-Controlled Generator)**:
   - Full generator suite (`Tree`, `Foliage`, `Ivy`, `Mushroom`, `Prop`), fully covered by existing 48+ unit tests (`smoke.py`, `frond_checks.py`, `plant_form_checks.py`).
   - Palm Frond: 1 continuous notched card per dahan with inverted-V roof crease (satisfies single-blade requirement).
2. **Engine B (Interactive Curve Trunks & Library Geometry Nodes Engine)**:
   - Powered by `landscapy/assets/landscapy_library.blend`, `landscapy/library.py`, and `landscapy/trees.py`.
   - Curve trunks that can be interactively edited in Edit Mode.
   - Modular foliage collections: `LeafSolid` (faceted clumps), `LeafDome` (anime cloud puffs), `LeafPalm` (continuous notched blades), `LeafBanana` (broad lamina), `Flowers` (4-triangle valley flowers), `Fruits` (banana bunch, coconut cluster), `Props` (rock, hollow trunk, mushrooms).
   - Driven by `LP_TreeEngine` Geometry Nodes with real-time viewport wind.

---

## 0.58.0 Preview

- Pine mengisi pucuk dan semua tingkat cabang utama sebelum menambah rumpun kedua pada satu tingkat. Kartu utama dan pengisi diposisikan lebih jauh dari batang agar pangkal cabang terlihat di sela lapisan. Sisi kartu melengkung turun dari tulang tengah dan tetap memakai satu pulau UV dengan 16 quad per kartu pada preset. Sebelas pemeriksaan TreeBough mencakup batas kartu, Trunk Clearance, Side Droop, paritas mesh/live, angin, dan save/reopen.
- Banana, Palm, dan Coconut memakai pelepah yang berurutan dari tua hingga muda di pucuk. Banana mempertahankan satu kartu gambar per helai. Palm dan Coconut memakai anak daun berpasangan yang terlipat mengikuti pelepah. Tandan pisang bawaan melengkung keluar dari batang semu lalu menjuntai ke bawah.
- Scene Eevee yang dapat diedit tersedia di `demo/pine_bough_v0580` dan `demo/tropical_crowns_v0580`. Audit visual keseluruhan katalog dan showcase toolkit masih berlangsung.

## 0.57.0 Preview

- Needle Spray memakai rumpun quad besar yang mengikuti cabang. Density terlebih dahulu mengisi pucuk dan tingkat utama, lalu menambah kartu di celah antar tingkat. Daun gantung menutupi bagian dalam tajuk dan sisakan bukaan di tepi luar.
- Tekstur starter Pine diganti dengan `Conifer_Bough_RGBA.png`. Regenerate memperbarui starter lama yang masih bawaan dan mempertahankan gambar serta material pengguna.
- Mode live dan mesh memakai susunan kartu yang sama. Density dan Limit berubah di Geometry Nodes. Perubahan bentuk, jumlah quad per rumpun, dan pengaturan gambar perlu Regenerate.
- Studi visual Pine ada di `demo/pine_bough_v0570`, bersama scene yang dapat diedit. Audit visual semua preset dan showcase toolkit masih berlangsung.

- Batang, cabang, dan akar digabung sebagai permukaan kayu sebelum kartu daun dibuat. Pangkal cabang melebar, ukuran cabang mengikuti ketebalan induknya, dan tiap cabang mempunyai lengkung tumbuh tersendiri. Akar gantung beringin berangkat dari bagian cabang yang masih tebal.
- Pemeriksaan Blender 5.2.2 atas kayu Pine, Broadleaf, Banyan, Banana, Coconut, Bonsai Tree, dan Mangrove tanpa daun menemukan satu komponen tertutup per aset. Pemeriksaan cabang lulus 11 kasus. Pine dengan kartu instanced menghasilkan 360 muka quad pada density 30.
- Preset Cloud memakai **Branch Canopy Masses**. Pengaturan **Cover Crown** yang sudah ada tetap tersedia dengan mematikan opsi tersebut.
- Close-up kayu adalah render kerja untuk memeriksa sambungan.

## Sisa pekerjaan: 5 workstream besar

1. Menuntaskan kualitas bentuk dan coverage untuk seluruh Plant/Leaf Type di banyak kombinasi konfigurasi; penghapusan kartu Mid/Low perlu terus melindungi coverage dan siluet dari beberapa arah.
2. Melengkapi distribusi live dan pertumbuhan Ivy di permukaan kompleks serta transisi antarobjek. Ivy statis kini menavigasi sudut dan celah terbatas; beberapa jalur live masih guide-projection.
3. Menuntaskan attachment deformasi, rebind topology, sistem angin hierarkis, dan penempatan buah/ornamen pada seluruh bentuk generator.
4. Menuntaskan Build/export game: penyederhanaan detail batang/props dan tekstur per versi, audit impostor/normal, laporan budget, serta interoperabilitas shader.
5. Melengkapi variasi/material props dan jamur, audit UI interaktif/undo, demonstrasi akhir, dokumentasi, dan pemeriksaan kompatibilitas Blender 5.2.

Versi 0.41–0.53 secara bertahap menambah Curve Path, Ivy, angin, frond, canopy controller, texture cards, dan bentuk tear. Versi 0.54 menambah hierarchy Plant Type → Trunk Type → Leaf Type → Fruit Type dan generator Fruit/Ornaments terpisah. Versi 0.55 membatasi pilihan per cabang hierarchy, menambah keluarga placement buah, serta mengaudit seluruh preset dalam gallery Eevee. Versi 0.56 menambahkan navigasi sudut dan gap bridge terbatas untuk Ivy statis, dengan uji visual Eevee dan suite regresi penuh. Kelima workstream masih berlangsung; paket ini belum memenuhi seluruh spesifikasi.

## Pembaruan 0.56.0 — Ivy surface navigation

- Pertumbuhan Ivy statis pada mesh kini berpindah di sudut antar-face tersambung dengan mengikuti tangent face baru. **Corner Angle Limit** dapat menolak perpindahan normal yang terlalu tajam.
- **Gap Bridge (Steps)** membatasi jangkauan pencarian ke island mesh terpisah. Saat BVH global memilih ulang island asal pada tepian, generator mencari island alternatif di dekatnya dan hanya menerima lompatan yang bergerak maju, memenuhi batas jarak, serta lolos ambang sudut. Nilai 0 tidak mengizinkan lompatan antar-island.
- Arah pertumbuhan mengikuti transformasi lokal generator, dan seed tetap deterministik. Mode Ivy Curve/Geometry Nodes live tetap memproyeksikan guide; navigasi sudut/gap baru ini khusus jalur seed-growth statis.
- `demo/ivy_navigation_v0560` menyertakan scene editable serta render Eevee yang memperlihatkan corner handoff dan lompatan gap 0,20 m dengan 3 langkah. Pemeriksaan khusus menguji sudut, batas sudut ketat, transformasi rotasi, bridge aktif/nonaktif, dan determinisme.
- Suite regresi Blender 5.2.2 lulus **557 pemeriksaan tanpa kegagalan**, termasuk demo plant catalog dan pemeriksaan fruit hierarchy. ZIP 0.56 lolos pemeriksaan arsip, pemasangan dan aktivasi di sandbox `BLENDER_USER_SCRIPTS` terisolasi, serta wiring properti panel. Render navigasi memakai Eevee; Flat bake dari rangkaian regresi tetap memakai GPU OptiX.
- TEMP/TMP untuk render dan tes diarahkan ke `.temp` di folder addon pada D:. Berkas recovery Blender `quit.blend` yang ditemukan di C: Temp dipindahkan tanpa dihapus ke `recovery/C_Temp_quit_2026-11-03.blend`; setelah pembersihan C: memiliki 53,82 GiB kosong dan tidak ada cache Landscapy yang tersisa pada C: Temp atau root drive.
- Batasan: Ivy tidak melakukan pencarian rute global, occlusion, atau deteksi rintangan; lompatan antar-surface hanya berlaku untuk island dalam jarak yang dikonfigurasi. Navigasi ini belum tersedia pada mode Geometry Nodes live.

## Pembaruan 0.55.0 — pilihan morfologi yang mengikuti Plant Type

- Panel Tree kini mengikuti hierarchy secara aktif. Trunk Type hanya menampilkan profil yang cocok untuk Plant Type; Leaf Type menaruh formasi yang direkomendasikan untuk profil tersebut di urutan pertama sambil tetap menyediakan formasi Tree lainnya sebagai pilihan stylized; Fruit Type mengikuti kelompok batang/cabang. Mengubah profil batang mengatur ulang susunan buah hanya jika pilihan lama tidak kompatibel. `AUTO` tetap memakai rekomendasi Plant Type.
- Fruit placement kini meliputi Banana Bunch, Axillary Fruit, Grape Cluster, Coconut Crown Cluster, Hanging Panicle, Raceme, Cauliflorous, Terminal Cluster, Axillary Pods, dan Conifer Cones. Starter editable baru tersedia untuk pod serta cone; kerucut dibuat dari skala low-poly. Buah tidak muncul otomatis sampai pengguna menyalakan Fruit dan membuat/menetapkan source.
- Dead Tree benar-benar memakai Leaf Type **None** dan tidak menghasilkan kartu daun. Banyan kini membangkitkan beberapa akar gantung dari cabang-cabang berbeda; sebelumnya kondisi terletak setelah loop dan sering tidak pernah terpicu.
- Scene editable dan render Eevee seluruh 19 preset ada di `demo/plant_catalog_v0550`; galeri 10 susunan buah berada di `demo/fruit_hierarchy_v0550`. Galeri memakai skala tile seragam hanya untuk perbandingan; ukuran asli tiap aset tersimpan pada pengaturan generator dan scene.
- Pada rilis 0.55, suite regresi Blender 5.2.2 lulus **555 pemeriksaan tanpa kegagalan**. Pemeriksaan mencakup preset 19/19, pilihan trunk/leaf/fruit yang mengikuti hierarki, akar, buah, angin, lampiran kartu, Build Variants, dan Flat bake GPU OptiX; ZIP 0.55.0 lulus pemeriksaan arsip serta pemasangan dan aktivasi pada `BLENDER_USER_SCRIPTS` terisolasi. Galeri buah Eevee menampilkan 10 susunan.
- Render/test `TEMP` dan `TMP` diarahkan ke `.temp` di folder addon pada D:. Pemeriksaan akhir menunjukkan C: memiliki 54.8 GiB kosong dan tidak berisi cache Landscapy yang dibuat di root drive.
- Batasan: setiap preset adalah morfologi stylized yang dapat diedit, bukan tiruan botani atau kultivar spesifik. Kepadatan kartu, bentuk tajuk, taper, ukuran, dan textures tetap perlu artist review pada kombinasi controller serta konfigurasi ekstrem.

## Pembaruan 0.54.0 — hierarki tanaman dan buah

- **Plant Type** kini mencakup Broadleaf, Banyan, Giant, Bonsai, Twisted Pine, Conifer/Pine, Palm/Coconut, Banana, Willow, Acacia, Baobab, Dead Tree, Mangrove, Apple, Mango, serta Grape Vine. Memuat preset memilih **Trunk Type** (atau AUTO), formasi **Leaf Type**, root defaults, Fruit Type yang disarankan, dan starter bark image. Trunk Type dapat dioverride; root style dan keluarga tekstur batang mengikuti pilihan tersebut. Hanya gambar starter yang ditetapkan addon yang diperbarui oleh pergantian preset. Gambar/material pengguna tetap dipertahankan.
- Struktur Tree kini memakai profil batang/cabang terpisah: whorl conifer dan leader, crown terminal Palm/Pseudostem, cabang stilt Mangrove, cordon Vine rendah, cabang melengkung Bonsai, serta layout Willow/Umbrella. Leaf Type tetap mandiri dan kartu daun tetap memakai Texture Slots ber-image sehingga bentuk dapat dipadukan tanpa menyebar kartu secara acak ke seluruh tajuk.
- **Fruit** dan **Ornaments** kini terpisah pada UI, source slots, density, batas, seed, transformasi, HSV, opacity, status, dan output. Fruit Type membatasi titik ke pseudostem atas (Banana Bunch), cabang sekunder (Apple/Axillary), ujung ranting (Grape Cluster), pangkal pelepah (Coconut Crown), atau panikel terminal (Mango). Raceme dan Custom Placement juga tersedia. Starter mesh dapat diedit atau diganti objek sendiri. Flower, Bud, dan Seed Pod tetap kategori Ornament. Sampling kedua kategori menghindari titik anchor yang terlalu berdekatan.
- Kedua kategori memakai binding barycentric/semantic branch dan pengaruh angin yang sama. Regenerate pohon memperbarui keduanya; Build High/Mid/Low membawa attachment masing-masing, mereduksi subset deterministic, serta mengubah resolusi teksturnya. Flat membake asset beserta attachment dengan GPU OptiX. Save/Load User Preset schema 4 memaketkan slot buah dan ornamen secara terpisah; schema 1–3 tetap didukung.
- Tes khusus di `tests/plant_hierarchy_fruit.py` memeriksa rekomendasi Plant/Trunk/Leaf/Fruit, lima aturan placement, pemisahan binding, preset portabel, dan empat Build Variant. Regresi Blender 5.2.2 lulus **536 pemeriksaan tanpa kegagalan**, termasuk bake GPU OptiX. ZIP 0.54.0 preview terpasang pada sandbox terisolasi; `tests/install_results.json` merekam hasilnya. Galeri Eevee preset/buah ada di `demo/plant_presets_v0540` dan `demo/fruit_hierarchy_v0540`; scene terpadu beserta sumber editable, Build Variants dan PNG Flat berada di `demo/integrated_v0540`.
- Koreksi visual terbaru: trunk biasa memakai texture grooves vertikal agar tidak tampak terpuntir; Pine memiliki whorl dan needle spray lebih rapat; pangkal crown Banana/Palm disebar sepanjang zona pucuk; akar stilt Mangrove lebih lebar dan tidak menambahkan fork radial otomatis. Galeri Eevee terakhir selesai sekitar 2.5 detik; render terintegrasi sekitar 3.7 detik dan Flat OptiX sekitar 6.6 detik.
- Batasan: fruit memakai source mesh starter atau objek kustom; generator belum mensimulasikan pembungaan/musim maupun botani spesies penuh. Banana, Coconut, Mango, Apple, dan Grape placement merupakan aturan stylized. Galeri bukan pembuktian bahwa setiap konfigurasi kustom akan selalu menghasilkan siluet yang benar; seluruh profil dan kombinasi pengguna masih memerlukan audit visual. Material stylized dapat diganti lewat Customize Surface.

## Pembaruan 0.53.0 — bentuk tepi Broad Lamina

- **Blade Edge Tear**, **Tear Frequency**, dan **Tear Seed** menambah takik asimetris pada kedua tepi Broad Lamina tanpa memindahkan tulang tengah. Jalur statis/individual dan live Geometry Nodes sama-sama mendukungnya. Seed tepi terpisah dari posisi, tekstur, warna, serta angin. UV, jumlah face, opacity, dan Build High/Mid/Low/Flat tetap dipertahankan.
- Uji khusus memeriksa perubahan live, seed independen, tulang tengah tetap, UV dan topology tetap, preset tersimpan, generator statis, Tree guide, Tree mesh, Foliage Curve dan mesh, serta Flat GPU. `demo/blade_tears_v0530` memuat scene editable, render Eevee, dan wireframe bilah. Ini menghasilkan takik stylized; robekan panjang yang terbelah dari tepi ke dekat tulang tengah dan bentuk pelepah kelapa sesuai referensi masih perlu pemolesan.

## Pembaruan 0.52.0 — controller mesh tajuk pada Tree live

- Tree dengan Leaf Type berpelepah atau Broad Lamina kini menerima controller mesh terbuka (Surface) atau tertutup (Volume) dalam jalur Geometry Nodes. Mesh controller menentukan titik tujuan tajuk; pangkal setiap rachis diambil dari permukaan batang/cabang terdekat sehingga kartu tidak melayang. ID cabang, level, posisi cabang, dan koefisien angin ikut disampel dari kayu. Bentuk controller, density, mask vertex group yang sudah dipilih, ukuran daun, dan angin bekerja live.
- Build High/Mid/Low/Flat mempertahankan source, menurunkan kayu, rachis, bilah dan tekstur, serta membake Flat dengan GPU OptiX. Surface plane, Volume tertutup, mode salah, mask, Texture Slots kustom, duplikasi, save/reopen, append, dan angin diuji. Perubahan nama mask, controller, pola, atau daftar tekstur tetap memerlukan Regenerate.
- `demo/live_tree_mesh_v0520` berisi Tree Surface Pinnate Frond dan Tree Volume Broad Lamina, render Eevee, serta wireframe. Dua gambar selesai sekitar 1,53 detik pada mesin uji. Pangkal dipilih dari kayu terdekat, sehingga tidak selalu cabang yang diinginkan secara artistik; pengendalian anchor per cabang dan pemolesan siluet masih terbuka.
- ZIP 0.52.0 berhasil diinstal/diaktifkan dalam Blender terpisah. Regresi Blender 5.2.2 lulus **511 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Pemeriksaan C: terakhir menunjukkan 55,32 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp; `.temp` addon sekitar 5,61 MB.

## Pembaruan 0.51.0 — bilah Banana live pada Tree

- Tree Banana kini memakai mesh batang/cabang/akar dan guide cabang ringkas untuk membentuk rachis serta bilah ribbon UV di Geometry Nodes. Width, detail rachis, density, Texture Slots RGBA kustom berbobot, dan angin dapat diubah live. Struktur cabang dan daftar Texture Slots tetap diperbarui melalui Regenerate.
- Sesuai klarifikasi referensi pengguna, pilihan **Leaf Type** memakai istilah morfologi: Broad Lamina, Pinnate Frond, dan Needle Spray. Tree Form Preset dan Leaf Type dapat dipilih terpisah; ID internal Banana/Palm/Conifer tetap dipakai agar file lama kompatibel. Uji menggabungkan batang Broadleaf dengan Broad Lamina serta batang Banana dengan Needle Spray. Radius rachis kini mengikuti Leaf Type yang dimuat, bukan nama preset batang.
- Build High/Mid/Low/Flat mereduksi detail kayu, sisi rachis, segmen bilah, tekstur, dan kartu sesuai aturan coverage; Flat dibake dengan GPU OptiX. Uji khusus mencakup duplikasi dengan guide tersendiri, save/reopen, append, dan instalasi ZIP terisolasi.
- `demo/live_tree_banana_v0510` berisi Conifer/Palm/Banana editable, render Eevee, dan wireframe yang memperlihatkan bilah Banana; dua gambar selesai sekitar 1,46 detik pada mesin uji. Batas selanjutnya: Tree dengan mesh canopy controller masih memakai jalur distribusi statis.
- ZIP 0.51.0 terpasang dan aktif dalam lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **501 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Pemeriksaan C: menunjukkan 57,34 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp; cache kerja berada di `.temp` addon (sekitar 5,6 MB).

## Pembaruan 0.50.0 — frond Tree berdaun tersusun live

- Tree dengan pola Opposite, Alternate, Spiral, Whorl, Conifer, atau Palm, tanpa mesh canopy controller, kini membuat batang/cabang/akar sebagai mesh Tree dan frond dari guide edge per cabang melalui Geometry Nodes. Kartu tidak lebih dulu dibangun penuh di Python. ID cabang, level, koordinat cabang, dan koefisien angin sampai ke kartu. Density, Count, lebar daun, sisi rachis, warna/opacity, seed, dan angin bekerja live; perubahan struktur kayu atau daftar Texture Slots memerlukan Regenerate.
- Build High/Mid/Low/Flat membekukan geometri live. Mid/Low membangun kayu lebih sederhana, mengurangi sisi rachis, memperkecil tekstur, dan menurunkan kartu sejauh aturan coverage mengizinkan. Ornamen live, gambar RGBA kustom berbobot, duplikasi dengan guide terpisah, Curve manual, save/reopen, dan append diuji. Mesh canopy controller tetap memakai jalur volume/surface lama; Banana Tree live ditambahkan pada 0.51.
- `demo/live_tree_fronds_v0500` memuat Conifer/Palm editable, render Eevee, serta wireframe kartu/rachis. Rachis Palm terhubung ke batang setelah radius guide diinisialisasi. Dua gambar Eevee membutuhkan sekitar 1,54 detik pada mesin uji. ZIP 0.50.0 berhasil diinstal/diaktifkan secara terpisah. Regresi Blender 5.2.2 lulus **492 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Pemeriksaan terakhir: C: memiliki 57,43 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp.

## Pembaruan 0.49.0 — raycast Ivy Curve ke mesh target

- Ivy Curve + target kini mempunyai Curve Surface Projection: Nearest Surface, Ray Down, dan Custom Ray. Mode ray memakai jarak Probe, offset dari normal hit, serta atribut `lp_surface_hit` untuk miss. Metode dipilih saat Regenerate; arah Custom, Probe, Curve, dan target dapat berubah live. Arah Custom nol didiagnosis tanpa mengganti source. Generator Ivy statis memakai pilihan proyeksi yang sama.
- Uji khusus membedakan tanah dan dinding yang sama-sama dekat, memeriksa arah ray, miss, transform target, jalur statis, Build empat versi termasuk Flat GPU OptiX, save/reopen, dan append. `demo/live_ivy_raycast_v0490` memuat scene editable, render Eevee, dan wireframe; dua gambar render membutuhkan sekitar 1,64 detik pada mesin uji. ZIP 0.49.0 berhasil diinstal/diaktifkan secara terpisah, termasuk pemeriksaan node raycast dari paket.
- Keterbatasan: titik guide yang miss tetap berada pada Curve dan spline belum otomatis dipotong pada rentetan miss. Navigasi sudut tajam, occlusion kompleks, dan jembatan celah masih terbuka. Regresi Blender 5.2.2 lulus **480 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Pemeriksaan terakhir: C: memiliki 57,44 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp.

## Pembaruan 0.48.0 — Banana live mesh dan pemeriksaan referensi angin

- Banana Foliage kini dapat menyebar rachis dan ribbon blade pada controller mesh Surface/Carpet atau Volume. Density, spacing, limit, controller, panjang, lebar, detail tangkai, droop, serta arah outward Volume bekerja live setelah Generate pertama. Radius spline hasil instancing diinisialisasi agar blade tidak runtuh menjadi bidang luas nol. Texture Slots RGBA, opacity, angin, UV, Build High/Mid/Low/Flat GPU, save/reopen, dan append diuji khusus.
- Video referensi `Blender Project/Ref/stylized tree wind.mp4` diperiksa ulang sebagai gerak hasil. Fase cluster, flutter per card, dan bobot ujung card yang sudah tersedia sejak 0.46 sesuai pola gerak yang dapat diamati. Rekaman 320×180 tidak memperlihatkan node/rig asli, sehingga implementasi tidak mengklaim menyalin setup pembuat video.
- `demo/live_banana_mesh_v0480` memuat scene editable, render Eevee Surface/Volume, dan wireframe ribbon. Render dua gambar membutuhkan sekitar 1,39 detik pada mesin uji. ZIP 0.48.0 berhasil diinstal/diaktifkan dalam lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **473 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Pemeriksaan terakhir: C: memiliki 57,44 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp.

## Pembaruan 0.47.0 — frond live pada mesh Surface dan Volume

- Pola Opposite, Alternate, Spiral, Whorl, Conifer, dan Palm kini dapat menyebar banyak rachis pada controller mesh terbuka atau volume tertutup. Geometry Nodes menghitung titik tumbuh dari density, spacing, mask, seed, dan limit; tiap titik menghasilkan rachis mesh beserta kartu daun tersusun. Edit controller, density, jumlah station, panjang, droop, sudut daun, dan detail tangkai memperbarui hasil tanpa Regenerate. Mengganti pola atau daftar Texture Slots masih membutuhkan Regenerate.
- Limit tetap membatasi kartu akhir, bukan hanya jumlah frond. Satu station tetap menghasilkan daun di ujung setelah bagian tangkai kosong. Atribut UV, alpha, warna, opacity, fase angin, serta slot gambar pengguna dipertahankan. Ornamen live mengikuti kartu dan density. High/Mid/Low mereduksi rachis dan kartu; Flat dibake pada pose netral dengan OptiX GPU.
- `demo/live_mesh_fronds_v0470` memuat scene editable, render Eevee Surface Palm dan Volume Conifer, serta wireframe kartu/tangkai. Banana pada mesh dan frond Tree live belum tersedia. Siluet Conifer/Palm dari mesh masih perlu pemolesan spesies.
- ZIP 0.47.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **467 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Demo Eevee merender 216 face kartu Palm Surface serta 352 face kartu Conifer Volume dalam sekitar 1,70 detik. Flat GPU OptiX, ornamen live, save/reopen, dan append diuji. Pada pemeriksaan terakhir C: memiliki 57,44 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp.

## Pembaruan 0.46.0 — sebaran ornamen live dan fase card berkelompok

- Ornamen Foliage/Ivy Live Geometry Cards kini disebar dari geometri kartu pada pose netral melalui Geometry Nodes. Perubahan density, limit, controller, serta rentang variasi warna/transformasi mengubah hasil tanpa Generate ulang. Pilihan source mesh berbobot tetap tersedia; mengganti sumber, bobot slot, atau zona sebaran memerlukan **Generate / Update Ornaments**. Child memakai gerak angin sumber secara terpisah dari rest proxy sehingga buah mengikuti kartu tanpa loncatan atau angin ganda. Build High/Mid/Low mengambil snapshot hasil aktual; Flat dibake pada pose netral GPU OptiX.
- Dari video referensi `Blender Project/Ref/stylized tree wind.mp4`, gerak yang bisa diamati adalah ayunan massa daun dengan perubahan kecil pada tiap card. Implementasi membagi `lp_cluster_phase` menurut cabang atau sel spasial, lalu menyimpan `lp_card_phase` tersendiri untuk flutter. Pangkal card tetap tertahan oleh `lp_leaf_wind`. Fase baru tersedia pada mesh penuh, card instanced, Foliage/Ivy live, dan blade Banana; shader game dapat memakai kedua atribut tersebut. Rekaman 320×180 tidak mengungkap graph animasi asli, sehingga pendekatan ini mencocokkan perilaku visualnya.
- Demo `demo/live_ornaments_v0460` berisi scene editable, render Eevee, dan wireframe. `demo/card_wind_v0460` berisi foliage carpet berornamen dan video 48 frame/24 fps; 32 ornamen mempertahankan ID dengan langkah maksimum sekitar 0,069 unit antarframe. `demo/card_wind_tree_v0460` berisi scene pohon, dua frame contoh, dan video Eevee 48 frame/24 fps pada 720×720. Render animasi carpet/pohon membutuhkan sekitar 13,02/13,45 detik pada mesin uji.
- ZIP 0.46.0 terpasang/aktif di Blender terpisah. Regresi Blender 5.2.2 lulus **455 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Flat GPU OptiX diuji lewat regresi. Video 800×534 terdekode 48 frame/24 fps. Pada pemeriksaan terakhir C: memiliki 57,41 GB kosong, tanpa `C:\Landscapy_Bakes`, `C:\quit.blend`, atau entri Landscapy di User Temp. Milestone pertama dan kelima belum selesai.

## Pembaruan 0.45.0 — ornamen pada live cards dan flutter per kartu

Perilaku ornamen dan fase card pada bagian ini adalah riwayat versi 0.45; versi 0.46 di atas menggantikannya.

- Foliage dan Ivy Live Geometry Cards kini dapat menghasilkan ornamen otomatis pada Surface, Volume, dan Curve Path. Ornament Update menyalakan topology penuh sebelum sampling dan binding; preview tetap memakai proxy terpisah. Controller dan angin menggerakkan ornamen melalui mesh evaluasi, sementara perubahan density/topology ditandai untuk Update Ornaments. Build menolak anchor usang, memasukkan ornamen ke High/Mid/Low dan Flat GPU.
- Berdasarkan video referensi `Blender Project/Ref/stylized tree wind.mp4` yang menampilkan gerak hasil (bukan graph node), flutter kini mengambil fase `lp_cluster_phase` per kartu dan menambah gerak kecil pada sumbu kedalaman di ujung kartu. Akar kartu tetap tertahan, gerakan per kartu tidak mengubah seed distribusi. Demo `demo/card_wind_v0450` menyertakan animasi Eevee dua detik; `demo/live_ornaments_v0450` memperlihatkan source editable, buah, render, dan wireframe.
- ZIP 0.45.0 terpasang/aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **441 pemeriksaan tanpa kegagalan**, lima gate GUI modal lulus, dan kedua scene demo dapat dibuka ulang dengan binding valid. Video Eevee 48 frame/24 fps terdekode dengan benar pada 800×534; render animasi sekitar 13,79 detik. Flat ornamen diuji dengan GPU OptiX. C: Temp sekitar 392,93 MB tanpa `C:\Landscapy_Bakes` atau `quit.blend`; `.temp` addon sekitar 1,99 MB dan frame sementara telah dibersihkan.
- Batasan: sebaran ornamen sendiri belum live ketika jumlah kartu berubah; perlu Generate / Update Ornaments. Binding barycentric mengikuti bentuk saat topology stabil, dan controller yang mengubah jumlah kartu membuat binding perlu diperbarui. Video referensi beresolusi 320×180 dan tidak memperlihatkan cara setup node, sehingga kesesuaian di sini bersifat visual.

## Pembaruan 0.44.0 — Growth Wander Ivy plane live

- Ivy Surface live pada mesh/plane kini meresample guide sulur utama sesuai Growth Step dan Growth Step Budget, lalu memberi pergeseran lateral halus berbasis noise deterministik. Growth Wander mengatur amplitudo, nilai nol menghasilkan guide lurus, dan pangkal serta ujung tidak bergeser. Cabang tumbuh dari tangent guide yang sudah dibentuk, kemudian sulur dan kartu diproyeksikan ke controller seperti sebelumnya.
- Uji khusus membandingkan guide lurus dan berkelok, hasil berulang, kontrol live, Build empat versi dengan Flat GPU, serta save/reopen. Demo `demo/live_ivy_wander_v0440` memuat scene editable, dua render Eevee, dan wireframe.
- ZIP 0.44.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **426 pemeriksaan tanpa kegagalan** dan lima gate GUI modal lulus. Render Eevee dua pose serta wireframe selesai sekitar 2,31 detik; Flat Build diuji dengan GPU OptiX. C: Temp sekitar 392,93 MB tanpa `C:\Landscapy_Bakes` atau `quit.blend`; `.temp` addon sekitar 1,08 MB.
- Batasan: wander masih membentuk guide sebelum proyeksi; belum mengarahkan pertumbuhan berdasarkan rintangan, menelusuri sudut tajam, atau menjembatani celah. Milestone ivy belum selesai.

## Pembaruan 0.43.0 — cabang Ivy plane live

- Ivy Surface live pada mesh/plane kini membuat cabang dari sulur utama dalam Geometry Nodes. Side Vines, Branch Interval, Branch Angle, Side Vine Length Ratio, dan Growth Wander mengubah jumlah, jarak, arah, panjang, serta variasi cabang tanpa Regenerate. Cabang memakai seed tersendiri untuk variasi sudut, diproyeksikan ke mesh, lalu mendapat sulur mesh dan kartu bertekstur. Atribut `lp_ivy_branch_index` membedakan batang utama (`-1`) dan tiap cabang.
- Uji khusus memeriksa jumlah nol sampai beberapa cabang, kontrol live, batas sampel, deformasi controller, normal kartu, Build empat versi termasuk Flat GPU, save/reopen, dan append. Demo `demo/live_ivy_branch_v0430` berisi scene editable, dua pose Eevee, serta wireframe. Proyeksi di luar probe tetap meninggalkan guide tanpa snap, sehingga ujung dekat tepi permukaan memerlukan inspeksi artistik.
- ZIP 0.43.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **424 pemeriksaan tanpa kegagalan**, lima gate GUI modal lulus, dan galeri Ivy cabang dapat dibuka ulang. Render Eevee dua pose dan wireframe selesai sekitar 2,22 detik; Flat Build diuji memakai GPU OptiX. C: Temp sekitar 392,93 MB tanpa `C:\Landscapy_Bakes`, `quit.blend`, atau file Landscapy baru; `.temp` addon sekitar 0,98 MB.
- Batasan: cabang masih berupa guide lurus yang diputar pada titik tumbuh; Growth Wander baru memvariasikan sudut per cabang, belum mengubah jalur secara bertahap. Raycast arah, navigasi sudut tajam/celah, dan ornamen otomatis belum selesai.

## Pembaruan 0.42.0 — Ivy target dan plane live

- Ivy Curve Path sekarang dapat memakai mesh Target. Geometry Nodes meresample guide sesuai Growth Step dan Growth Step Budget, mencari permukaan terdekat dalam Surface Search Distance, lalu memproyeksikan sulur dan daun dengan Surface Offset. Normal permukaan mengarahkan kartu secara lokal; ini memperbaiki daun edge-on pada plane horizontal. Edit Curve, target, mesh melengkung, offset, dan probe langsung memperbarui hasil. Guide yang berada di luar probe tetap tidak menempel dan membawa atribut `lp_surface_hit=false`.
- Ivy dengan Controller mesh/plane dalam mode Surface/Auto membuat satu guide dari Growth Seed, Growth Direction, dan Length. Arah diproyeksikan ke bidang singgung; bila sejajar normal, fallback tangensial dipakai. Deformasi plane, seed, arah, panjang, density, resolusi sampel, dan batas sampel bekerja live. Build High/Mid/Low/Flat, GPU OptiX, tekstur RGBA kustom, save/reopen, serta append diuji. Dua scene editable dengan render Eevee dan wireframe berada di `demo/live_ivy_target_v0420` dan `demo/live_ivy_plane_v0420`.
- ZIP 0.42.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **422 pemeriksaan tanpa kegagalan**, lima gate GUI modal lulus, dan kedua demo Ivy dapat dibuka ulang. Render Eevee target/plane masing-masing sekitar 2,78/2,15 detik; Flat Build diuji memakai GPU OptiX. C: Temp sekitar 392,93 MB tanpa `C:\Landscapy_Bakes`, `quit.blend`, atau file Landscapy baru; `.temp` addon sekitar 1,08 MB.
- Batasan: Ivy plane live belum menumbuhkan cabang atau wander; pertumbuhan hanya sepanjang satu guide awal. Proyeksi target memakai nearest surface dengan batas jarak, belum raycast arah, navigasi sudut tajam, atau pemecahan segmen saat keluar dari probe. Target terpisah untuk Controller mesh dan ornament otomatis masih membutuhkan jalur Regenerate.

## Pembaruan 0.41.0 — Conifer, Palm, dan Banana Curve Path live

- Pola Conifer dan Palm kini memakai jalur rachis dan kartu daun live yang sama dengan pola berpasangan. Banana mempunyai graph Geometry Nodes tersendiri: satu blade ribbon UV bertekstur dan tangkai mesh per spline Curve. Edit Curve, lebar/taper, petiole, droop, bend, twist, valley, density nol, serta limit memperbarui hasil tanpa Regenerate. Texture Slots RGBA dan bobot, opacity, seed terpisah, preview, dan angin tersedia. Mengganti pola, gambar, atau daftar slot masih membutuhkan Regenerate.
- Build High/Mid/Low menurunkan sisi tangkai dan segmen memanjang blade Banana; Flat dibake GPU OptiX. Uji khusus mencakup struktur dua sampai dua belas spline, edit live, kontrol bentuk, tekstur pengguna, angin, empat versi, save/reopen, dan append. Galeri `demo/live_frond_advanced_v0410` mempunyai scene editable, render Eevee (sekitar 1,69 detik), dan wireframe untuk ketiga pola.
- ZIP 0.41.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **408 pemeriksaan tanpa kegagalan** dan lima pemeriksaan GUI modal lulus. Render Eevee galeri selesai dalam sekitar 1,69 detik; Flat Build diuji dengan GPU OptiX. C: Temp sekitar 386,27 MB, tanpa `C:\Landscapy_Bakes` atau `quit.blend` baru; `.temp` addon sekitar 1,12 MB.
- Batasan: satu spline adalah satu frond; Banana tidak memakai Count sebagai distribusi banyak frond. Frond pada mesh Surface/Volume atau Tree dan ornamen otomatis belum live. Tampilan Conifer/Palm masih perlu pemolesan agar siluet spesies lebih meyakinkan.

## Pembaruan 0.40.0 — pola frond Curve Path live

- Generator Foliage live pada Curve Path sekarang menerima Opposite, Alternate, Spiral, dan Whorl. Geometry Nodes membangun tangkai mesh dan kartu daun dari setiap spline; edit Curve, density, spacing, count, limit, petiole, ukuran/sudut/taper daun, droop, radius/tip/sisi/segmen tangkai, serta radius titik Curve memperbarui hasil tanpa Regenerate. Pangkal kartu berbagi sway tangkai dan tidak menerima flutter ganda.
- Rachis memakai resample berdasarkan Rachis Segments. Arah droop menginterpolasi gravity dengan arah lateral saat tangent mendekati vertikal agar tidak muncul tekukan mendadak. Build Mid/Low mengambil snapshot dengan sisi profil tangkai lebih sedikit; pemilihan kartu tetap melindungi alpha-visible coverage. Uji khusus mencakup empat pola, kontrol live, tekstur RGBA pengguna, seed independen, preview, diagnosis mode, angin, Build High/Mid/Low/Flat GPU, save/reopen, dan append. Galeri editable, render Eevee, dan wireframe ada di `demo/live_frond_path_v0400`.
- Batasan: Curve guide mewakili satu rachis per spline, bukan distribusi banyak frond pada mesh Surface/Volume. Conifer, Palm, Banana, frond pada Tree, dan ornamen otomatis belum memakai jalur live. Mengganti pola atau Texture Slots membutuhkan Regenerate. Count menjadi batas station per spline; panjang tangkai diatur dengan Curve.
- ZIP 0.40.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **400 pemeriksaan tanpa kegagalan**, lima skenario GUI modal lulus, serta galeri empat pola dapat dibuka ulang dan dievaluasi ketika addon aktif sebelum membuka scene. Render Eevee galeri selesai dalam sekitar 1,61 detik; Flat Build memakai GPU OptiX. C: Temp tetap sekitar 386,65 MB, tanpa `C:\Landscapy_Bakes` atau `quit.blend` baru; file sementara uji sekitar 1,11 MB berada di `.temp` addon.

## Pembaruan 0.39.0 — detail sulur Ivy High/Mid/Low

- Kontrol **Vine Radial Sides** ditambahkan untuk Ivy Path live dan generator Ivy biasa. Ivy live memperbarui profil sulur di Geometry Nodes tanpa Regenerate; Ivy biasa menerapkannya saat Regenerate. Default High live sekarang 12 sisi. Build Mid/Low menyalin graph sementara dan memakai profil lebih sederhana sesuai rasio, tanpa mengubah sumber editable atau High.
- Pada uji Ivy dua spline, profil High/Mid/Low berisi 12/6/3 sisi dan triangle sulur turun 72/36/18. Ditemukan dan diperbaiki kesalahan pemilihan kartu: snapshot Geometry Nodes membawa `UVMap` tanpa layer aktif, sehingga pemeriksaan alpha dahulu memakai UV (0,0) dan menganggap seluruh kartu transparan. Sekarang UVMap dipakai sebagai fallback; demo Eevee/wireframe `demo/ivy_lod_v0390` mempertahankan 71 dari 72 kartu daun pada Mid/Low sambil menurunkan face sulur 1.728/864/432. Uji khusus memeriksa alpha-visible coverage, kontrol live, penurunan face sulur, sumber High, Flat GPU, save/reopen, dan append. Panjang sulur masih mengikuti resolusi spline controller, sehingga pengurangan segmen longitudinal belum tersedia.
- ZIP 0.39.0 terpasang dan aktif dari lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **389 pemeriksaan tanpa kegagalan**, lima skenario GUI modal lulus, dan scene demo dapat dibuka ulang. Render Eevee perbandingan selesai dalam sekitar 1,43 detik; Flat Bake memakai GPU OptiX. C: Temp tetap sekitar 386,65 MB, tanpa `C:\Landscapy_Bakes` atau `quit.blend` baru; file sementara sekitar 1,14 MB berada di `.temp` addon.

## Pembaruan 0.38.0 — sulur dan kartu Ivy Path live

- Generator Ivy dengan Curve controller, mode Path/Auto, Instanced Card Source, dan Live Geometry Cards sekarang membuat sulur mesh serta kartu daun dalam satu graph Geometry Nodes. Edit spline langsung mengubah kedua bagian. Leaf Spacing, Leaf Size, Leaf Spread Angle, Vine Radius, dan Density dapat diubah tanpa Regenerate; Ivy biasa juga memakai Leaf Spread Angle saat Regenerate. Pangkal kartu mewarisi bobot sway sulur dan flutter lokal tetap nol pada pangkal.
- Uji khusus memeriksa beberapa spline, edit Curve, angin, parameter live, gambar RGBA pengguna dan bobot beberapa slot, opacity, preview, diagnosis target, Build empat versi termasuk Flat GPU, save/reopen, serta append. Demo editable dan dua render Eevee berada di `demo/live_ivy_v0380`.
- Batasan: live Ivy baru mengikuti Curve tanpa target surface, pertumbuhan cabang, atau ornamen otomatis. Mid/Low mengurangi kartu dan resolusi tekstur tetapi tabung sulur masih memakai detail mesh yang sama. Pertumbuhan surface/plane dan target snap tetap memakai generator lama dengan Regenerate. Mengganti daftar slot tekstur atau rentang variasi juga membutuhkan Regenerate.
- ZIP 0.38.0 terpasang dan aktif di lingkungan Blender terpisah; regresi Blender 5.2.2 lulus **388 pemeriksaan tanpa kegagalan** dan lima skenario GUI modal lulus. Dua render Eevee demo selesai dalam sekitar 2,33 detik total; Flat Build diuji dengan GPU OptiX. C: Temp sekitar 386,65 MB, tanpa `C:\Landscapy_Bakes` atau `quit.blend` baru; file sementara pengujian sekitar 1,14 MB berada di `.temp` addon.

## Pembaruan 0.37.0 — kartu Path live pada Curve

- Live Geometry Cards pada Foliage menerima Curve controller dalam mode Path/Auto. Curve to Points menghitung station per spline dari Density dan Spacing; kartu mengikuti tangent lokal. Beberapa spline Poly/Bezier, perubahan titik kurva, density, spacing, limit, seed, preview, dan Build High/Mid/Low/Flat tersedia tanpa Regenerate setelah graph dibuat. Density nol menghasilkan nol kartu. Curve dengan bevel/extrude ditolak sebelum mengganti sumber agar tidak menghasilkan graph kosong diam-diam.
- Uji khusus memeriksa multi-spline, arah kartu, edit controller, density/spacing/limit/seed, diagnosis mode/bevel, preview, Build Flat GPU, save/reopen, dan append. Scene `demo/live_path_v0370` menyimpan dua pose editable dan render Eevee; kartu 160→165 dan sulur contoh mengikuti perubahan Bezier tanpa Regenerate. Sulur contoh memakai mesh GN terpisah dari controller centerline.
- Batasan: Spacing mengatur interval sepanjang spline, bukan jarak Euclidean antar kartu di tikungan atau persilangan. Position Jitter dapat mengurangi jarak akhir. Foliage Path belum menjadi generator Ivy live lengkap: pertumbuhan permukaan, cabang sulur, dan ornamen otomatis tetap melalui Regenerate. Curve/Path pada Tree dan Ivy sendiri juga belum live.
- ZIP 0.37.0 terpasang dan aktif dari lingkungan Blender terpisah, termasuk pembuatan kartu Path langsung dari paket terpasang. Regresi Blender 5.2.2 lulus **375 pemeriksaan tanpa kegagalan** dan lima skenario UI modal lulus. Dua render Eevee Path selesai sekitar 2,35 detik. C: Temp sekitar 386,65 MB; tidak ada `C:\Landscapy_Bakes` atau `quit.blend` baru; file sementara uji sekitar 1,07 MB berada di `.temp` addon.

## Pembaruan 0.36.0 — Volume live pada mesh tertutup

- Live Geometry Cards pada Foliage sekarang menerima controller Volume/Auto tertutup. Mesh to Volume dan distribusi titik volume berjalan di Geometry Nodes; controller mesh/shape key, density, spacing, limit, seed, dan detail grid mengubah hasil tanpa Regenerate. Spacing nol memakai sebaran acak; spacing positif memakai grid deterministik dengan penipisan menurut density. Jumlah sel dibatasi melalui Volume Grid Detail 16–128, default 64. Jarak grid efektif tercatat dalam atribut `lp_distribution_spacing`; mask vertex group diproyeksikan dari permukaan terdekat.
- Mesh terbuka ditolak untuk Volume, dan mesh tertutup tanpa volume mendapat diagnosis. Controller yang disembunyikan dari render tetap menyuplai kartu. Build High/Mid/Low memakai satu snapshot volume live, Flat dibake dengan GPU OptiX, dan append serta save/reopen mempertahankan relasi controller dan kartu. Scene `demo/live_volume_v0360` memiliki dua render Eevee yang memperlihatkan tajuk mengikuti shape key: 780→812 kartu, posisi paling kanan 1,581→1,973 tanpa Regenerate.
- Batasan: density volume berupa perkiraan akibat voxelisasi dan batas grid; Position Jitter dapat mengurangi jarak akhir. Mode Auto dipilih ulang saat Regenerate bila topology berubah. Algoritma Volume live belum melakukan pencarian penutup celah tajuk. Frond tersusun, ornamen otomatis, Curve/Path, Tree, dan Ivy belum live. Detail shader game dan audit visual spesies masih terbuka.
- ZIP 0.36.0 terpasang dan aktif dalam lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **361 pemeriksaan tanpa kegagalan**; lima skenario GUI modal juga lulus. Dua render Eevee scene Volume selesai sekitar 2,43 detik. C: Temp sekitar 386,65 MB, tanpa `C:\Landscapy_Bakes` atau `quit.blend` baru; file sementara pengujian sekitar 1,11 MB tersimpan di `.temp` addon.

## Pembaruan 0.35.0 — kartu Surface live

- Foliage pada controller mesh terbuka kini mempunyai opsi **Live Surface Cards** bersama Instanced Card Source. Geometry Nodes menempatkan dan membentuk kartu langsung dari controller; mesh sumber tetap tanpa face. Perubahan mesh/shape key controller, Density, Spacing, Limit, seed kategori, dan preview dievaluasi tanpa Regenerate. Quad, Valley/Peak acak, beberapa gambar RGBA pengguna, opacity, UV, warna, ukuran, angin, mask, serta Build High/Mid/Low/Flat tersedia. Mid/Low mengambil snapshot distribusi live yang sama sebelum seleksi kartu penjaga cakupan.
- Uji khusus mencakup controller edit, density live, independensi seed, gambar pengguna, random shape, mask, duplikasi driver, preview, angin nol/aktif, Build GPU, save/reopen, dan append. Scene editable dan dua render Eevee pada `demo/live_surface_v0350` memperlihatkan shape key controller di dua frame; jumlah face dan tinggi foliage berubah tanpa Regenerate.
- Batasan: hanya Foliage Surface/Auto dengan controller mesh dan tanpa ornamen otomatis; pola frond tersusun, Volume, Path, Tree, dan Ivy tetap memakai generator lama. Mengganti gambar/slot, rentang randomisasi, atau bentuk kartu memerlukan Regenerate untuk membangun ulang graph. Pengujian UI interaktif menyeluruh dan shader game masih terbuka.
- ZIP 0.35.0 terpasang dan aktif dalam lingkungan Blender terpisah. Regresi Blender 5.2.2 lulus **349 pemeriksaan tanpa kegagalan**, dan lima skenario GUI modal lulus. Render Eevee dua pose selesai sekitar 2,4 detik pada scene contoh. C: Temp sekitar 386,65 MB; tidak ada `C:\Landscapy_Bakes` atau `quit.blend` baru; file sementara pengujian sekitar 1,14 MB berada di `.temp` addon.

## Pembaruan 0.34.0 — Undo/Redo Build melalui UI Blender

- Uji Blender berjendela menemukan Build modal belum membuat checkpoint Undo: satu Undo setelah Build menghapus variant sekaligus generator sumber. Operator kini membuat checkpoint sebelum Build; Undo menghapus hanya keluaran, Redo mengembalikannya.
- Lima skenario GUI tersembunyi lulus: Create dan Regenerate modal dengan progress serta Undo/Redo; Build tunggal dengan Undo/Redo; Esc pada Build setelah keluaran parsial muncul; dan Build Collection dua generator serta satu kubus biasa dengan Undo/Redo. Uji Esc memakai `--enable-event-simulate`. Pengujian ini melengkapi regresi headless, belum mencakup setiap tombol dan kombinasi panel.
- Runner GUI memakai TEMP/TMP dan bake dalam folder addon. `quit.blend` lama dari C: Temp dipindah ke `recovery/C_Temp_quit_2026-11-02.blend` tanpa menghapus data pemulihan.
- ZIP 0.34.0 terpasang/aktif dalam lingkungan addon terpisah. Regresi headless Blender 5.2.2 lulus 333 pemeriksaan; kelima gate GUI dijalankan ulang dan lulus. Setelah pengujian, C: Temp sekitar 386,27 MB, tidak ada `C:\Landscapy_Bakes` atau `quit.blend` baru di C, dan cache GUI sekitar 1,07 MB berada di `.temp` addon.

## Pembaruan 0.33.0 — titik Surface dari Geometry Nodes

- Foliage Surface/Carpet kini dapat memilih sampling titik Geometry Nodes. Mesh controller dievaluasi dan ditriangulasi sementara agar normal kartu cocok dengan segitiga tampilan. Density memakai luas dunia, Mask membaca vertex group, Spacing memilih Poisson, Limit serta Seed diterapkan. Hasil titik diteruskan ke sistem kartu dan tekstur yang sudah ada; opsi Instanced Card Source tetap bekerja. Scene editable/render Eevee di `demo/gn_surface_v0330` memuat bunga Valley dengan dua tekstur dan tallgrass pada permukaan melengkung.
- Sepuluh uji khusus memeriksa determinisme, luas dunia, mask, spacing, normal mesh melengkung, transform nonuniform, beberapa tekstur, Build High/Mid/Low/Flat GPU, save/reopen, serta pembersihan data sementara. Distribusi belum hidup langsung saat controller digeser: titik masih dibaca Python saat Regenerate, dan mode Volume/Path belum memakai sampling GN ini.
- Flat Bake Directory dapat diatur. Build dengan path relatif pada scene yang belum disimpan kini berhenti dengan pesan jelas, tanpa menulis ke akar drive C. Runner mengarahkan bake uji ke folder addon. Sebanyak 90 PNG bake lama (3,3 MB) dipindahkan dari `C:\Landscapy_Bakes` ke `recovery/C_Drive_Landscapy_Bakes` dalam addon; gambar Flat yang dipakai scene telah di-pack.
- Regresi Blender 5.2.2 lulus 333 pemeriksaan tanpa kegagalan dan ZIP 0.33.0 terpasang/aktif dalam lingkungan terpisah. Setelahnya, `C:\Landscapy_Bakes` tidak ada, C: Temp sekitar 387,45 MB, dan `.temp` addon kosong.

## Pembaruan 0.32.0 — morfologi akar

- Akar otomatis kini berawal lebih dekat sisi batang, menjalar mendatar lebih awal, dan ujungnya dapat ditanam. Buttress diberi pelebaran vertikal pada pangkal alih-alih lengkungan tabung tinggi. Taper default melambat dan kontrol Departure, Tip Burial, Buttress Height, serta posisi/sudut/jangkauan/lebar fork tersedia di panel Root System.
- Render Eevee dan scene editable perbandingan Surface, Buttress, dan Exposed berada di `demo/roots_v0320`. Enam uji khusus memeriksa geometri akar, kontrol fork, independensi tajuk, determinisme, curve manual, dan save/reopen. Sambungan akar dengan batang dan persimpangan fork masih memakai irisan mesh; gaya Exposed tetap sengaja menonjol dari tanah.
- Semua proses Blender lewat runner lokal menggunakan `.temp` di folder addon untuk TEMP/TMP, sehingga tidak membuat folder kerja baru di C: Temp.
- Regresi Blender 5.2.2 lulus 323 pemeriksaan tanpa kegagalan. ZIP 0.32.0 berhasil dipasang dan diaktifkan pada lingkungan addon terpisah. Setelah pengujian, C: Temp tetap sekitar 387,4 MB dan `.temp` di folder addon kosong.

## Pembaruan 0.31.0 — kartu bersubdivisi dan Banana terinstans

- Foliage, Tree, dan Ivy menerima mode Instanced Card Source untuk Quad, Valley/Peak, kartu grid bersubdivisi sampai 12, serta blade Banana. Satu titik sumber per kartu membawa ID, slot, warna, opacity, dan atribut angin; buffer titik tanpa face menyimpan posisi vertex detail. Geometry Nodes merealisasikan template per topology/UV/material dan mengambil offset vertex dari buffer. Kayu dan sulur tetap sebagai mesh sumber.
- Pengujian membandingkan geometri, UV, material, ID, dan bobot angin dengan mesh biasa; preview menipiskan kartu utuh, angin menggerakkan hasil, duplikasi membuat buffer sendiri, mode mesh membersihkan buffer lama, dan source bertahan saat append/save/reopen. Foliage bersubdivisi dan Banana dengan ornamen menghasilkan High/Mid/Low/Flat termasuk bake GPU OptiX. Pada 12 subdivision, beda koordinat terbesar yang teramati sekitar 0,00001 unit karena presisi float Blender.
- Scene editable dan render Eevee ada di `demo/instanced_subdivided_v0310`: 178 kartu bunga sebagai titik tanpa face sumber serta tujuh blade Banana sebagai titik di samping mesh kayu. Distribusi masih dilakukan Python; generator sementara masih membangun mesh penuh dan buffer tetap menyimpan posisi tiap vertex, sehingga ini belum memenuhi distribusi Geometry Nodes penuh.
- Regresi Blender 5.2.2 lulus 317 pemeriksaan tanpa kegagalan; ZIP 0.31.0 terpasang dan aktif pada lingkungan addon terpisah dengan pemeriksaan buffer kartu bersubdivisi. Scene terpadu dapat dibuka ulang setelah bake lama dibersihkan.
- Runner regresi, instalasi, dan skrip Blender tunggal kini mengarahkan TEMP/TMP ke `.temp` di folder addon. Autosave Landscapy 9,6 MB dipindah dari C: Temp ke `recovery`; dua file ekstraksi installer yang sudah tidak aktif dibersihkan secara terpisah sehingga C: Temp turun sekitar 780 MB menjadi 387 MB. Penghapusan seluruh folder ekstraksi secara rekursif ditolak peninjauan otomatis, sehingga sisa folder dibiarkan.

## Pembaruan 0.30.0 — frame kontinu pada props kayu

- Pembentuk loft untuk Stump, Fallen Trunk, Broken Branch, dan Root memakai frame ring kontinu yang sama dengan batang pohon. Algoritma lama dapat melompat 92–180° antar ring pada contoh jalur lurus sampai bengkok; frame baru memiliki perubahan maksimum 6,23° pada jalur uji yang paling bengkok. Bentuk, UV silindris, material ujung kayu, dan jumlah poligon tetap mengikuti pengaturan High/Mid/Low.
- Galeri Eevee serta `.blend` editable enam props dibuat ulang di `demo/wood_frames_v0300`. Uji khusus memeriksa empat jalur, orientasi ring, face, dan UV. Aset lama membutuhkan Regenerate dan Rebuild agar mesh menggunakan pembentuk baru.
- Regresi Blender 5.2.2 lulus 290 pemeriksaan tanpa kegagalan, termasuk tes loft baru dan pembukaan ulang scene terpadu. ZIP 0.30.0 terpasang serta aktif pada lingkungan addon terpisah.
- Uji append scene kompleks dari `demo/integrated_v0290` ke file baru memeriksa sembilan generator, Root Curves, carpet/ivy controller, buah terikat, target snap, Wind Controller bersama, gambar yang dapat ditemukan, Regenerate setelah append, empat collection variant, serta save/reopen termasuk path PNG Flat. Sepuluh pemeriksaan otomatis ini lulus; pengujian interaktif melalui dialog Blender masih perlu.

## Pembaruan 0.29.0 — scene demonstrasi terpadu

- Scene editable dan render Eevee terpadu kini ada di `demo/integrated_v0290`. Isinya beringin dengan buah terikat dan Wind Controller bersama, bonsai dengan empat spline Root Curves, kelapa dengan leaflet tersusun, bunga Valley serta tallgrass pada mesh terbuka melengkung, ivy pada Curve, boulder dengan jamur Parasol yang snap dan glow di bawah cap, dan hollow log.
- Beringin mempunyai High/Mid/Low/Flat dalam collection terpisah; Flat dibake dengan GPU OptiX dan PNG alpha. Render galeri Eevee menyembunyikan variant agar tidak bertumpuk. Laporan menyimpan durasi render/bake dan face tiap variant. Uji otomatis membuat scene, memeriksa 12 kondisi, membuka ulang `.blend`, lalu memeriksa delapan relasi yang harus tetap hidup. Runner regresi sekarang menolak JSON hasil lama walau Blender keluar dengan kode 0.
- Regresi Blender 5.2.2 lengkap lulus 289 pemeriksaan tanpa kegagalan, termasuk scene terpadu dan perbandingan pucuk; setiap hasil JSON terbukti baru. ZIP 0.29.0 berhasil dipasang, diaktifkan, dan dinonaktifkan/diaktifkan ulang pada lingkungan addon terpisah.
- Pemeriksaan ulang scene akar 0.26 menghasilkan render pucuk sebelum/sesudah Regenerate di `demo/tip_v0290`. Cincin visual pada gambar lama tidak tampak setelah Regenerate 0.29. Orientasi ring maksimum di batang lama 68,1° dan di mesh baru 0,47°; enam segmen teratas pada mesh lama hanya berubah sampai 2,44° per ring, jadi cincin lama bukan bukti puntiran aksial yang terlokalisasi tepat di pucuk. File `.blend` hasil Regenerate ikut disimpan.
- Visual akar dan sambungan akar-batang masih perlu pemolesan: sistem curve dan kontrol bentuk sudah tersedia, tetapi beberapa kombinasi dapat tampak terlalu tebal atau seperti duri. Scene terpadu ini membuktikan komposisi dan portabilitas, belum berarti semua kualitas visual serta seluruh rencana telah selesai.

## Pembaruan 0.28.0 — orientasi ring batang stabil

- Puntiran aksial yang terlihat pada batang biasa adalah bug orientasi ring mesh, bukan gaya default. Sebelum perbaikan, ring bertetangga pada garis batang lurus dapat berbeda 180°; pada contoh batang bengkok perbedaan sesaat mencapai 88°. Frame baru mengikuti jalur secara kontinu untuk batang, cabang, akar, dan props tube. Pengaturan Curve masih membengkokkan garis tengah sesuai pilihan pengguna.
- Uji frame memeriksa batang lurus serta tiga tingkat bengkokan dan mengukur perbedaan ring maksimum sesudah perbaikan 3,5° pada kasus uji. Regresi Blender 5.2.2 lulus 267 pemeriksaan tanpa kegagalan; ZIP 0.28.0 terpasang dan aktif pada lingkungan addon terpisah. Render Eevee dan scene editable ada di `demo/trunk_v0280`; render akar curve juga diperbarui. Scene lama membutuhkan Regenerate dan Rebuild agar mesh mengikuti perbaikan.

## Pembaruan 0.27.0 — akar dengan curve yang dapat diedit

- Root System menerima objek Curve terpisah. Setiap spline terbuka membentuk akar; mode Automatic Only, Auto + Curves, dan Curves Only tersedia. Tombol **Create Editable Root Curves** menyalin jalur akar primer saat ini ke objek curve dalam collection pohon, mengaktifkan Curves Only, dan mempertahankan sumber prosedural.
- Regenerate membaca curve dievaluasi dengan transformasi objek, membalik spline bila arah titiknya menuju batang, serta membangun ulang mesh akar, UV, graph, fork, dan LOD. Guide Ground Follow opsional mencampur tinggi jalur dengan raycast Ground Mesh. Seed akar tidak memindahkan titik curve manual. Demo Eevee dan `.blend` editable ada di `demo/root_guides_v0270`.
- Uji khusus mencakup edit spline, orientasi terbalik, mode hybrid/auto/curve, tombol pembuatan, pembatalan konfigurasi yang keliru, terrain, Build Variants, save/reopen, dan append collection dengan curve ke file baru. Regresi Blender 5.2.2 lulus 265 pemeriksaan tanpa kegagalan; uji append tambahan juga lulus dan ZIP 0.27.0 terpasang pada lingkungan addon terpisah. Curve yang benar-benar menyatu dengan batang sebagai permukaan watertight masih belum tersedia.

## Pembaruan 0.26.0 — Root System pohon

- Akar pohon radial lama yang menyerupai duri diganti jalur akar melengkung yang menipis dan memiliki fork. Tiga gaya Surface, Buttress, dan Exposed memberi bentuk dasar berbeda. Kontrol pengguna mencakup jumlah, panjang, variasi panjang, lebar, tip, taper, spread, wander, arch, embed, flatten, fork, segmen, serta seed akar terpisah.
- Ground Mesh opsional diikuti melalui raycast; kontrol follow dan offset mengatur kedekatannya dengan permukaan. Beberapa preset pohon mengisi nilai akar yang sesuai dan semua parameter dapat diedit. Root System menyimpan ID cabang negatif, UV, dan atribut yang selamat dari save/reopen. High/Mid/Low membangun tingkat detail akar berbeda; Flat tetap dibake pada GPU OptiX.
- Uji Blender mencakup jalur tube halus tanpa sambungan putus, bentuk dan UV, seed, preset, lereng tanah, LOD, bake GPU, serta save/reopen. Regresi Blender 5.2.2 lulus 263 pemeriksaan tanpa kegagalan dan ZIP 0.26.0 terpasang pada lingkungan addon terpisah. Render Eevee dan scene editable ada di `demo/roots_v0260`. Akar dan batang masih berpotongan sebagai komponen mesh terpisah; sambungan watertight dan pembimbingan akar langsung dengan curve belum selesai.

## Pembaruan 0.25.0 — sumber instansi untuk bentuk kartu

- Quad bertaper/twist/bend serta Valley/Peak empat triangle kini menyimpan satu titik per kartu dengan offset vertex. Geometry Nodes membangun ulang bentuk hasil mesh biasa, termasuk UV, material, ID, dan bobot angin. Tree/Ivy mempertahankan kayu atau sulur, dan Palm leaflet Quad dapat diinstansikan. Uji mencakup Individual, surface, Tree, Ivy, Palm, preview kartu utuh, Build, angin, serta rollback bila Banana blade yang bersubdivisi belum didukung.
- Banana blade, kartu dengan subdivision lebih dari satu, dan bentuk frond yang membutuhkan lebih dari lima vertex per kartu masih memakai mesh sumber penuh. Pembuatan sementara di Python masih menghasilkan geometri penuh sebelum commit.
- Regresi Blender 5.2.2 lulus 256 pemeriksaan tanpa kegagalan; ZIP 0.25.0 terpasang dan aktif di lingkungan addon terpisah. Scene dan render Eevee `demo/instanced_shapes_v0250` menampilkan 211 titik bunga Valley tanpa face sumber dan Palm dengan 264 titik leaflet serta 1.684 face kayu.

## Pembaruan 0.24.0 — ornamen pada sumber Quad terinstans

- Tree, Ivy, dan Foliage Quad terinstans kini dapat menghasilkan ornamen otomatis dari slot objek. Penempatan menggunakan mesh hasil evaluasi lengkap. Target binding tetap pada density penuh; proxy viewport tersendiri menipiskan kartu sehingga perubahan Preview Cards tidak mengubah topology atau posisi ornamen.
- Uji khusus mencakup Tree, Ivy, surface foliage, preview berubah dan toggle, angin, Build empat versi, duplikasi, serta save/reopen. Mode ini menambah biaya evaluasi ketika ornamen aktif karena binding memerlukan geometri penuh. Kartu Valley dan frond kompleks belum didukung oleh sumber instansi.
- Regresi Blender 5.2.2 lulus 252 pemeriksaan tanpa kegagalan; ZIP 0.24.0 terpasang dan aktif di lingkungan addon terpisah. Scene dan render Eevee `demo/instanced_ornaments_v0240` menampilkan pohon dengan 900 kartu daun sebagai titik, 3.000 face kayu, serta 65 buah yang terikat.

## Pembaruan 0.23.0 — instansi Tree/Ivy dan batas perubahan siluet LOD

- Sumber Tree dan Ivy kini dapat menyimpan kayu atau sulur sebagai mesh solid serta satu titik per kartu Quad persegi panjang. Geometry Nodes merealisasikan kartu saat render/Build; Preview Density menyaring kartu tanpa menghilangkan kayu. Tes khusus membandingkan face, UV, material, ID cabang, atribut angin, dan Build dengan hasil mesh penuh.
- LOD Mid/Low mempertahankan kartu yang memberi cakupan besar pada siluet, termasuk lobe tunggal yang sebelumnya dapat dianggap tonjolan. Kandidat tonjolan hanya dihapus jika kehilangan piksel siluet tidak lebih dari 1% per kartu dan 2% kumulatif pada masing-masing sembilan proyeksi. Pengisi lubang dan lapisan inti tetap dilindungi; target rasio dilaporkan tidak tercapai bila syaratnya tidak mungkin.
- Mode instansi masih terbatas pada Quad datar persegi panjang tanpa subdivision dan belum mendukung ornamen otomatis. Proxy 128×128 dari sembilan arah tetap perlu inspeksi visual untuk sudut kamera lain.
- Regresi Blender 5.2.2 lulus 244 pemeriksaan tanpa kegagalan; ZIP 0.23.0 terpasang dan aktif di lingkungan addon terpisah. Render Eevee dan scene editable ada di `demo/lod_v0230` serta `demo/instanced_wood_v0230`. Tree instansi contoh menyimpan 800 kartu sebagai titik bersama 3.000 face kayu; viewport 25% menampilkan 190 kartu dan render memakai 800. Ivy menyimpan sulur 582 face dan 25 kartu instansi.

## Pembaruan 0.22.0 — sumber foliage Quad terinstans

- Foliage Quad persegi panjang tanpa subdivision kini dapat menyimpan satu titik per kartu. Geometry Nodes membuat kartu dari template berbagi sambil membawa UV, texture slot, warna, opacity, ID, dan atribut angin. Preview menipiskan titik secara deterministik di viewport tanpa proxy mesh penuh; render memakai semua titik. Mode ini opt-in.
- Build Variants merealisasikan High dan membangun Mid/Low/Flat dari density penuh; preview sumber tetap pada rasio pilihannya sesudah Build. Attachment manual ke mesh target, duplikasi, save/reopen, append collection ke file baru, serta perpindahan kembali ke mesh biasa diuji. Perpindahan controller/generator yang langsung diikuti Generate kini memperbarui matriks transform sebelum distribusi.
- Demo Eevee `demo/instances_v0220` menunjukkan 1.156 titik sumber, 0 face sumber, 211 face viewport pada preview 20%, dan 1.156 face High/render. Regresi Blender 5.2.2 lulus 238 pemeriksaan tanpa kegagalan; instalasi ZIP 0.22.0 terpisah lulus. Pembuatan sementara masih menggunakan Builder mesh penuh; evaluasi render dan Build tetap membutuhkan geometri penuh. Mode ini belum berlaku untuk Tree/Ivy, Valley, frond kompleks, Quad dengan taper/twist, atau ornamen otomatis.

## Pembaruan 0.21.0 — pilihan tekstur solid stylized

- Sebelas gambar RGBA orisinal 512×512 ditambahkan untuk beberapa gaya bark, kayu potong, batu, cap jamur, dan moss. Panel Textures memberi pilihan Stylized Look tersendiri pada setiap peran permukaan. Menerapkannya adalah tindakan eksplisit, sehingga gambar atau material pengguna tidak tertimpa saat menu diubah.
- Gambar dipack ke `.blend`; tint/HSV dan kanal material lain tetap dapat diedit. Build Mid/Low menurunkan resolusi gambar pustaka seperti gambar kustom. Uji Blender memeriksa peran terpisah, gambar pengguna, Build, dan save/reopen. Galeri Eevee dan scene editable ada di `demo/surface_library_v0210`. Regresi Blender 5.2.2 lulus 228 pemeriksaan tanpa kegagalan; instalasi ZIP 0.21.0 di lingkungan terpisah juga lulus.
- Preview mesh biasa masih berbagi mesh penuh dengan sumber; jalur instansi pertama untuk Foliage Quad tersedia sejak 0.22, tetapi Tree/Ivy dan bentuk kartu lain belum ikut.

## Pembaruan 0.20.0 — kedalaman cakupan kartu Mid/Low

- High tetap memakai mesh dan resolusi gambar sumber. Mid/Low membentuk ulang geometri kayu/props serta membuat salinan gambar statis pada skala resolusi yang dapat diatur (default 50%/25% per dimensi).
- Seleksi kartu Mid/Low memeriksa alpha dari sembilan arah. Kandidat hanya kartu transparan atau kartu yang jelas menonjol dari area inti. Kartu yang menutup celah atau membentuk siluet inti tetap dipertahankan. Lapisan terakhir pada tiap piksel inti tidak boleh dihapus; kehilangan piksel lapisan kedua dibatasi 2% per arah.
- Rasio kartu dan batas triangle tetap bersifat target; ketika pengurangan mengorbankan penutup tajuk, laporan menyatakan target tidak tercapai. Laporan mencatat kehilangan lapisan kedua per arah. Uji sintetik mencakup penonjolan, penutup lubang, dua lapis inti, dan variasi kecil siluet. Proxy 128×128 belum menjamin tampilan dari setiap sudut kamera.
- Regresi final Blender 5.2.2 lulus 224 pemeriksaan tanpa kegagalan. Instalasi ZIP 0.20.0 di lingkungan addon terpisah lulus. Render Eevee dan scene editable ada di `demo/lod_v0200`: pohon High/Mid/Low memakai 8.692/2.272/1.244 triangle kayu, tekstur berskala 100%/50%/25%, dan Mid/Low mempertahankan 2.161 dari 2.200 kartu. Rasio kartu 50%/20% dilaporkan tidak tercapai karena kartu yang tersisa masih menjaga cakupan.

## Pembaruan 0.19.0 — Create/Regenerate bertahap dan Undo

- Tombol Create dan Regenerate dari UI kini menjalankan pembentukan kartu per 128 kartu dengan kemajuan dan Esc sebelum commit. Create yang dibatalkan membuang objek sementara; Regenerate yang dibatalkan mempertahankan mesh, graph cabang, UID, dan status sebelumnya. API Python/background tetap sinkron melalui `generate()` atau dapat memakai iterator `generate_steps()`.
- Uji `tests/generate_progress_results.json` memeriksa cancel setelah tiga batch, kesamaan geometri dengan Generate sinkron, pemulihan pada error, prop solid, dan pembersihan Create yang dibatalkan. Uji Blender berjendela tersembunyi `tests/create_modal_gui_results.json` dan `tests/generate_modal_gui_results.json` membuktikan mode modal, progress, serta satu langkah Undo/Redo setelah selesai. Pengiriman Esc lewat UI belum diuji end-to-end.
- Perhitungan controller/tajuk sebelum kartu dibangun, attachment/ornamen/preview setelah commit, dan bake Flat OptiX masih berjalan sebagai langkah utuh; Esc ditangani di antara langkah tersebut. Operasi lain seperti preset dan rebind masih sinkron.

## Pembaruan 0.18.0 — tajuk lebih menutup dari beberapa arah

- Sampling Cover Crown kini membandingkan beberapa calon posisi per kartu pada grid sembilan proyeksi dan memilih yang lebih banyak mengisi area belum tertutup. Lobe pengisi tengah tetap mendapat alokasi khusus. Kontrol Gap Search Samples memiliki rentang 1–8 dan default 4.
- Estimasi anggaran kartu membaca alpha pada UV region, Opacity Map, opacity slot/kartu, dan mode cutout. Gambar transparan meminta lebih banyak kartu selama Limit memungkinkan. Posisi tetap deterministik dan seed warna/tekstur tidak mengubah distribusi.
- Enam render Eevee pada `demo/canopy_v0180` memakai jumlah 1.900 kartu yang sama. Empat kandidat menaikkan jumlah piksel alpha terlihat 5,52%/4,75%/6,60% pada arah 0°/90°/180° untuk scene contoh. Celah masih mungkin ada saat Limit tidak cukup atau dari sudut lain; optimasi memakai grid proxy, bukan visibility final kamera. Regresi Blender 5.2.2 lulus 217 pemeriksaan tanpa kegagalan.

## Pembaruan 0.17.0 — lima batu parametrik

- Pebble, Boulder, Flat Rock, Shard, dan Stack sekarang memiliki geometri yang berbeda. Shard memakai profil kristalin bersudut; Flat Rock dan Stack berupa lempeng tertutup. Proporsi, detail facet, erosi, retakan, dan sebaran lumut dapat diubah sebelum Generate/Build.
- Rock, Cracks, dan Moss adalah tiga peran material yang dapat dikustomisasi secara terpisah dengan gambar atau material pengguna. High default boulder memiliki 1.280 triangle, Shard 520, Flat Rock 968, dan Stack 2.904 pada contoh galeri; Mid/Low menurunkan geometri serta resolusi gambar sesuai konfigurasi.
- `demo/rocks_v0170` berisi scene editable, render Eevee, dan laporan jumlah triangle serta wajah material. Lima pemeriksaan di `tests/rock_results.json` menguji manifold, bentuk, kontrol, material kustom, Build GPU, dan save/reopen. Regresi Blender 5.2.2 lulus 210 pemeriksaan tanpa kegagalan.

## Pembaruan 0.16.0 — ekspor game dan seleksi kartu penjaga siluet

- High/Mid/Low/Flat hasil Build dapat diekspor sebagai empat GLB dengan gambar terkemas dan manifest JSON. UV, vertex color, serta atribut mask/fase angin `_LP_*` ikut dibawa. Flat delapan arah membawa atlas, ID per tampilan, dan metadata impostor. Ekspor membekukan attachment pada frame saat ini dan menonaktifkan angin prosedural untuk pose netral. Shader angin dan pemilihan impostor di game engine belum tersedia.
- Seleksi kartu Mid/Low memakai mask alpha sembilan arah yang juga menutup celah sempit terbuka di antara area tajuk utama. Kartu yang menutup celah atau menjaga siluet utama dipertahankan; detail menonjol dan kartu transparan tanpa cakupan dapat dikurangi. Laporan mencatat piksel mask utama dan cakupan tampak sebelum/sesudah per arah. Ini tetap proxy 128×128, sehingga visual pada sudut kamera penting perlu diperiksa.
- Uji GLB memeriksa empat keluaran, tekstur bertingkat sesuai LOD, ornamen, atribut, roundtrip import, dan atlas delapan arah dengan normal opsional. Uji LOD sintetik menambah celah terbuka serta kartu transparan. Regresi Blender 5.2.2 lulus 205 pemeriksaan tanpa kegagalan. Galeri Eevee, wireframe, scene, laporan, dan empat GLB pohon versi ini ada di `demo/lod_v0160`.

## Pembaruan 0.15.0 — kemajuan dan pembatalan Build

- Build Variants/Collection kini memakai operator modal saat dijalankan dari UI dan menampilkan kemajuan per High/Mid/Low/Flat. Esc membatalkan di antara versi. API Python/background tetap sinkron dan mencatat kemajuan lewat status Blender.
- Hasil baru disiapkan sebelum keluaran lama diganti. Pembatalan membersihkan hasil sementara aset aktif; keluaran lama, laporan, dan PNG Flat lama tetap ada. Aset batch yang telah selesai sebelum Esc tidak di-rollback. Render OptiX yang sedang berjalan belum bisa dipotong menjadi langkah lebih kecil.
- `tests/build_progress_results.json` memeriksa pembatalan setelah Low, propagasi pembatalan batch, serta commit empat versi. Uji Blender berjendela tersembunyi di `tests/build_modal_gui_results.json` membuktikan klik/invoke modal, empat langkah, bake Flat OptiX, dan penyelesaian operator. Regresi Blender 5.2.2 lulus 200 pemeriksaan tanpa kegagalan; rinciannya ada di `tests/regression_results.json`.

## Pembaruan 0.14.0 — props kayu parametrik

- Stump, Fallen Trunk, Broken Branch, Root, dan Vine kini mempunyai bentuk parametrik berbeda; Vine mengikuti Curve bila diberikan. Hollow Log berupa tabung horizontal dengan rongga serta permukaan bagian dalam, bukan tabung tertutup biasa.
- Wood, Cut Wood, dan Inner Wood adalah peran material terpisah sesuai tipe prop. Pola lingkar tumbuh default pada bidang potong dapat diganti gambar atau material sendiri. UV silindris pada bark dan UV planar pada ujung/rim mendukung tekstur pengguna. Load Prop Shape Defaults memberi ukuran awal tanpa menghapus kustomisasi.
- Semua enam bentuk edge manifold sebagai komponen mesh; akar dan ranting tambahan masih saling berpotongan dengan badan. Detail solid High/Mid/Low menurun bertahap. Scene dan dua render Eevee ada di `demo/wood_props_v0140`; tujuh uji khusus ada di `tests/wood_props_results.json`. Regresi keseluruhan Blender 5.2.2 lulus 197 pemeriksaan tanpa kegagalan; rinciannya ada di `tests/regression_results.json`.

## Pembaruan 0.13.0 — detail solid dan LOD yang menjaga cakupan

- Detail mesh kayu/props/jamur default High meningkat; Mid/Low membentuk ulang geometri solid menurut rasio detail, bukan hanya menghapus kartu daun. Contoh galeri: kayu pohon 8.692/2.272/1.244 triangle pada High/Mid/Low; batu 320/80/20 dan jamur 780/224/68.
- Mid/Low membuat salinan material dan gambar statis yang lebih kecil, termasuk gambar dalam node group dan normal map. Default skala tiap dimensi 50%/25%. Salinan dipack dan sumber tidak berubah; gambar UDIM/sequence/movie/viewer belum dapat diresize otomatis.
- Kartu diseleksi menurut cakupan alpha dan opacity dalam sembilan proyeksi. Pengisi lubang dan kartu penyangga siluet utama dipertahankan; kartu dekoratif yang menonjol dapat dilepas. Rasio/triangle budget yang menuntut penghapusan kartu penting dilaporkan belum tercapai. Ini pendekatan raster proxy, bukan jaminan pixel-perfect di semua kamera.
- Scene editable, galeri Eevee, wireframe, laporan triangle/tekstur, dan bake Flat GPU OptiX ada di `demo/lod_v0130`. Uji unit sintetik memeriksa kartu penonjol dan pengisi lubang; uji integrasi memeriksa geometri, multi-tekstur, material node group, rebuild, serta save/reopen. Regresi Blender 5.2.2 lulus 190 pemeriksaan tanpa kegagalan; rinciannya ada di `tests/regression_results.json`.

## Pembaruan 0.12.0 — angin hierarkis

- Kontrol Trunk / Stem Sway, Branch Bend, Cluster Sway, dan Leaf Flutter terpisah pada generator serta Shared Wind Controller. Cabang anak mewarisi fase dan displacement pada titik sambungan induk; pangkal kartu tetap tertahan saat cluster sway/flutter.
- Mesh menyimpan koefisien fase cabang dan kartu. High/Mid/Low mempertahankan atribut tersebut; Flat hanya memakai sway sederhana. Binding ornamen mengikuti target yang sudah bergerak tanpa local wind ganda secara default.
- Scene editable, dua still Eevee, dan MP4 24 frame berada di `demo/wind_hierarchy_v0120`. Sembilan pemeriksaan khusus mencakup kontinuitas cabang, kontrol terpisah, angin nol, seed, Shared Controller, binding, kartu, dan save/reopen. Regresi penuh kini 182 pemeriksaan tanpa kegagalan pada Blender 5.2.2, termasuk bake Flat OptiX.
- Batasan: angin ini adalah deformasi stylized sederhana, belum simulasi cabang fisik atau shader untuk game engine. Angin pada billboard Flat tetap tidak mewakili gerak internal cabang.

## Pembaruan 0.11.0 — cabang dan attachment semantik

- Levels 1–4 kini membuat hierarki cabang nyata dengan parent ID stabil untuk seed yang sama. Curve controller dapat memandu batang dan beberapa cabang melalui pilihan Auto, Hybrid, atau Curve Only.
- Mesh pohon/kartu membawa `lp_branch_id`, `lp_branch_level`, dan `lp_branch_t`; metadata jalur disimpan pada generator. Ornaments dapat dibatasi ke ID cabang yang dipilih dari face Object/Edit Mode.
- Mesh yang di-Bind manual pada pohon menyimpan koordinat jalur dan dapat menyesuaikan posisi serta anchor ketika cabang yang sama berubah setelah Regenerate. Cabang yang dihapus menghasilkan status invalid dan meminta Rebind. Binding mesh luar masih bergantung pada topology.
- Dua scene editable dan dua render Eevee ada di `demo/branches_v0110`. Sebelas pemeriksaan cabang mencakup hierarki, spline, ornamen, angin, binding lintas regenerate, empat varian termasuk bake OptiX, dan save/reopen. Total regresi kini 173 pemeriksaan tanpa kegagalan pada Blender 5.2.2.
- **Crown Join** menambah lobe pengisi interior pada Broadleaf, Banyan, Giant, dan Baobab sehingga kelompok cabang lebih tersambung. Nilai dapat diatur sampai nol untuk mempertahankan pad tajuk terpisah; pengisian masih dibatasi Limit dan alpha gambar. Satu pemeriksaan canopy baru menegaskan pengisian tidak mengubah struktur cabang.
- Batasan: ID cabang manual bergantung pada urutan spline. Penyederhanaan kayu pada LOD dan kualitas pengisian tajuk yang sama dari semua sudut masih terbuka. Angin hierarkis dasar ditambahkan pada 0.12.

## Pembaruan 0.10.0 — bunga dan tajuk spesifik

- Empat tekstur RGBA stylized orisinal ditambahkan: Flower Single, Flower Cluster, Willow Cluster, dan Acacia Cluster. Seluruh starter dipack saat dipakai; Texture Slots tetap bebas diganti atau dicampur dengan gambar serta material pengguna.
- Pattern Flower otomatis memilih kartu Valley empat triangle, tetap bisa diubah ke Quad. Perubahan pattern dan preset mengikuti gambar starter tunggal yang belum dimodifikasi, tanpa menimpa gambar kustom atau kombinasi multi-slot.
- Willow membentuk ranting gantung dan lobe tajuk vertikal; Acacia membentuk cabang radial dengan lobe payung yang datar. Scene dan lima render Eevee ada di demo/special_foliage_v0100, termasuk tampilan samping dan wireframe kartu bunga.
- Tujuh pemeriksaan baru di tests/special_foliage_results.json menguji alpha/pack, pola bunga, tekstur kustom berbobot, perbedaan siluet, seed, High/Mid/Low/Flat GPU, serta save/reopen.
- Batasan: penutupan tajuk tetap dibatasi Limit dan perkiraan coverage kartu transparan. Tekstur khusus bagi spesies/flower lain serta audit game shader masih terbuka.

## Pembaruan 0.9.0 — preview density aman untuk binding

- Tree, Foliage, dan Ivy memiliki Preview Density serta Preview Cards pada panel Distribution. Geometry Nodes menyaring kartu utuh berdasarkan ID stabil pada objek proxy viewport, sementara mesh sumber tetap penuh untuk render, attachment, ornamen, dan Build Variants.
- Regenerate menyinkronkan proxy; slider rasio berubah tanpa mengacak posisi kartu. Source ditampilkan sebagai bounding box ketika preview aktif dan kembali ke display semula setelah preview dimatikan. Proxy disembunyikan dari render dan tidak ikut Build Collection.
- Tujuh pemeriksaan di tests/preview_results.json menguji sumber penuh, subset deterministik, Foliage/Ivy, binding ornamen dan mesh luar, High/Flat GPU, serta save/reopen. Scene dan render perbandingan Eevee ada di demo/preview_v090.
- Batasan: mesh sumber tetap berada di memori; ini belum instancing/distribution Geometry Nodes. Interaksi viewport langsung dan efek pada scene sangat besar belum diaudit.

## Pembaruan 0.8.0 — impostor delapan arah

- Build Flat memiliki mode Single View (default) dan Eight Azimuth Views. Mode kedua membake delapan warna/normal opsional pada pose netral dengan OptiX GPU, atlas 4×2, dan edge dilation per tile.
- Metadata JSON dan properti objek mencatat azimuth lokal, UV region, ukuran atlas, extent, dan ruang normal per view. Gambar di-pack dalam .blend serta disimpan terpisah untuk game.
- Mesh Flat multi-sudut mempunyai delapan face; Geometry Nodes menampilkan satu face yang dipilih handler menurut arah scene camera saat render, dan arah viewport terakhir yang digerakkan saat orbit Perspective/Orthographic. Uji pindah kamera, viewport perspective/ortho, normal atlas, save/reopen, dan render dari empat arah ada di tests/impostor_results.json serta demo/impostor_v080.
- Append collection ke file baru telah diuji: controller, generator dan tekstur kustom yang di-pack tetap terhubung, regenerate mengubah density, serta Flat yang di-append memilih sudut kamera. Hasil ada di tests/append_results.json.
- Regresi otomatis versi 0.8 mencakup 161 pemeriksaan tanpa kegagalan pada Blender 5.2.2, termasuk bake OptiX. Total terbaru tercatat pada pembaruan 0.12 dan tests/regression_results.json. Polling orbit viewport diuji pada fungsi pemilihnya; interaksi UI langsung masih perlu diaudit.
- Batasan: beberapa viewport dengan arah berbeda berbagi satu face aktif; tile per-view tetap gambar pose netral sehingga animasi internal cabang tidak ada. Resolusi tinggi memakai memori besar; belum ada progress/cancel atau audit shader game.

## Pembaruan 0.7.0 — jamur dan snap

- Keluarga jamur memiliki profil parametrik yang lebih berbeda. Morel memanjang dengan kontur berlekuk, Coral bercabang, Bracket/Oyster memakai cap kipas, dan gills/underside mempunyai material terpisah.
- Kontrol baru: stem taper, bend randomness, cap rim/facets/rings, gill count, cluster spread, auto-bend menuju world-up, dan random crown tilt. Seed tetap deterministik.
- Snap memilih raycast down/custom atau nearest pada evaluated mesh, membatasi jarak, dan mempertahankan posisi saat target tidak terkena. Mushroom baru dari mesh terpilih mengisi Target otomatis. Snap mengorientasikan batang pada normal; auto-bend mengarahkan cap secara terpisah.
- Glow Under/Cap/All memakai area undersurface/cap/stem yang berbeda. Semua material tetap dapat diganti dengan tekstur atau shader sendiri.
- Galeri dan render Eevee sepuluh keluarga di demo/mushrooms_v070; 9 uji geometri, parameter, cluster, glow, snap, GPU Build Variants, preset, dan save/reopen di tests/mushroom_results.json.
- Batasan: tidak mengklaim setiap spesies biologis. Auto-bend belum menangani benturan crown dengan lingkungan; snap adalah operasi eksplisit, ikatan deformasi memakai Bind terpisah.

## Pembaruan 0.6.0 — angin dan batas LOD

- Shared Wind Controller Empty memiliki panel UI. Gust, turbulence, dan flutter kartu memakai Geometry Nodes; mask `lp_leaf_wind` membuat pangkal daun tetap tertahan. Response/phase offset per aset dan pilihan untuk memakai controller atau pengaturan lokal.
- Mid/Low mendukung batas jumlah triangle opsional. Kartu dan ornamen diambil sebagai unit utuh, lalu laporan menampilkan triangle body/ornamen/total dan `limit_met`. Batas di bawah biaya batang dan satu kartu dilaporkan tidak tercapai; batang sumber tidak dirusak.
- Bake Flat GPU OptiX mengisi RGB di belakang tepi alpha pada PNG warna dan normal tanpa mengubah alpha; normal map tetap opsional. Uji GPU memeriksa hasil alpha dan RGB transparan.
- Scene dan render Eevee tersedia di demo/wind_v060, termasuk MP4 dua detik dengan 32 frame. Uji angin, bake, dan batas triangle ada di tests/wind_bake_results.json serta variant_budget_results.json.
- Batasan: struktur batang tidak disederhanakan pada LOD; gust/turbulence prosedural sederhana dan shader game belum tersedia. Hierarki sway batang/cabang ditambahkan pada 0.12. RGB edge dilation tidak mengganti kebutuhan menguji tekstur di mesin game.

## Pembaruan 0.5.0 — frond, ivy, dan variasi kartu

- Palm/Banana/Conifer dan pola Opposite/Alternate/Spiral/Whorl memakai rachis dengan daun tersusun, bukan sebaran cluster. Banana satu blade lebar; kontrol jumlah, lebar, taper, sudut, petiole, droop, segmen, dan seed. Preset pohon Palm/Banana/Conifer/Twisted Pine memakai geometri ini.
- Density controller curve dihitung per panjang spline hasil evaluasi Bezier/Poly/NURBS; spline tidak tersambung satu sama lain. Mode distribusi salah didiagnosis.
- Ivy surface memakai seed, arah, raycast projection, branching terbatas, offset, dan penghentian di tepi/gap. Curve path dapat diproyeksikan pada mesh. Individual ivy tersedia. Ini pertumbuhan stylized berbasis langkah, bukan simulasi tanaman.
- Lima tekstur starter RGBA baru, tetap dapat ditimpa/dicampur dengan gambar dan material pengguna. Hanya starter image yang belum disentuh mengikuti perubahan preset.
- Card Tip Taper, rentang random bend/valley, tint, axis scale, serta seed terpisah. Valley positif sekarang menonjol ke arah normal kartu.
- Wind Direction kini memutar sway. LOD menjaga minimal satu kartu utuh untuk aset kecil; GPU Flat diuji pada palm, banana, dan ivy.
- Demo Eevee dan scene editable berada di demo/fronds_v050 dan demo/ivy_v050. 30 pemeriksaan baru tercatat di tests/frond_results.json, ivy_results.json, foliage_control_results.json, dan frond_variant_results.json.
- Batasan: frond belum memiliki angin per leaflet/tulang daun; seed ivy menggunakan nearest awal dan raycast tiap langkah, bukan pemecahan celah/occlusion rumit. Mesh controller pada pohon berfrond belum membentuk frond sepanjang controller mesh.

## Pembaruan 0.4.0 — ornamen dan binding deformasi

- Multiple source meshes berbobot; density/spacing/zona/rentang tinggi/limit, seed terpisah untuk distribusi, pilihan, transformasi, dan HSV/opacity.
- Starter berry dan flower editable; generator otomatis hanya Tree/Foliage/Ivy, tidak Individual.
- Binding barycentric Geometry Nodes mengikuti transform dan deformasi evaluated target. Triangle anchor rigid menjaga bentuk tiap ornamen; local wind tambahan opt-in.
- Pemeriksaan hash connectivity mendeteksi perubahan topology, termasuk vertex/face count sama; fallback rest pose dan Rebind. Dependency cycles ditolak.
- Regenerate membangun ulang ornamen/anchor. High/Mid/Low mempunyai child ornamen terikat ke body masing-masing, mempertahankan binding eksternal source, dan mengurangi ornament instance utuh. Flat menyertakan ornamen.
- Preset schema 3 membawa source objects di resource .blend, bersama gambar dan materials.
- Uji attachment, ornamen, LOD/binding, preset, serta demo Eevee dan video angin tersedia di tests dan demo/ornaments_v040.
- Batasan: auto tint menyisip ke top-level Principled (custom shader dapat membaca atribut); density memakai luas face, belum mask pixel alpha. Binding cabang semantik ditambahkan pada 0.11.

## Pembaruan 0.3.0 — bounded canopy coverage

- Sebaran Gaussian tanpa batas digantikan mode Cover Crown: lobes ellipsoid saling bertumpang tindih, shell/interior fill, sample directions merata, dan orientasi kartu ke luar.
- Anggaran dibagi merata ke seluruh cluster sebelum hard limit; tidak memotong semua daun cabang terakhir ketika limit rendah.
- Berlaku untuk tree cluster dan cloud bush tanpa controller; controller mesh dan distribusi non-cloud tetap memakai mode sebelumnya.
- Kontrol coverage/radius/shell/alignment, pilihan legacy, dan pemberitahuan limit tersedia.
- Preview Eevee diperiksa dari sudut 0, 90, 180 derajat. 14 pemeriksaan clustering tercatat dalam tests/canopy_results.json.
- Coverage memakai perkiraan luas kartu, belum optimasi pixel alpha atau occlusion dari semua sudut kamera.

## Pembaruan 0.2.0 — semua permukaan dapat dikustomisasi

- Bark, wood, rock, stem, mushroom cap/gills, dan tiap slot foliage mendukung image pengguna atau material Blender sendiri.
- Base color, normal UV, roughness, height/bump, opacity, emission; tint/HSV, mapping scale/offset/rotation, UV/Box, dan parameter noise dasar.
- Custom material nodes dipertahankan saat regenerate; perubahan bentuk preset tidak menghapus texture slots.
- UV non-foliage tidak lagi nol; batang/cabang memiliki unwrap silindris.
- Preset schema 2 membawa resource .blend dengan packed images dan custom materials, termasuk image di nested node groups.
- Mid/Low memakai penanda kartu sehingga textured bark tidak ikut dianggap kartu foliage.
- 14 pemeriksaan material/preset/UV/LOD/save-reopen tambahan terdapat dalam tests/texture_results.json.

## Diimplementasikan dan diuji awal

- Registrasi addon Blender 5.2; panel Create/Shape/Distribution/Textures/Variation/Attachments/Wind/Build.
- Generator mesh pohon, foliage cards, props, serta sepuluh keluarga bentuk jamur.
- Dua belas konfigurasi preset pohon; JSON preset pengguna.
- Auto surface/volume, density area/volume/path, spacing, mask vertex group surface, batas jumlah.
- Multiple image slots, weighted selection, aspect, pivot, UV region, alpha cutout/soft.
- Seed independen untuk warna, orientasi, tekstur; size, HSV, opacity, jitter.
- Quad dan Valley empat triangle; subdivision, bending, curl, twist.
- Angin Geometry Nodes dasar dengan shared controller.
- Build High/Mid/Low/Flat, deterministic card thinning, billboard PNG dan normal opsional, GPU OptiX.
- Demo editable dan render GPU; 41 smoke checks dalam tests/results.json.

## Ada implementasi, belum memenuhi cakupan/kualitas rencana

- Cabang: hierarki dan spline panduan tersedia; sambungan kayu, proporsi tiap spesies, dan kontrol lengkung cabang anak masih perlu dipoles.
- Willow/Acacia kini mempunyai bentuk tajuk dan gambar khusus; kualitas cabang sekunder, overlap kartu, serta variasi antar-seed masih perlu ditingkatkan.
- Binding barycentric, deteksi topology, dan remap cabang semantik dasar tersedia; deformasi nonrigid pada mesh luar dan pergantian urutan spline belum diaudit penuh.
- Snap berbasis raycast/nearest dan threshold random crown sudah ada; belum alat drag interaktif langsung di viewport.
- Ivy statis kini menavigasi sudut dan gap kecil memakai tangent handoff dan pencarian island terbatas. Ivy Geometry Nodes live masih memproyeksikan guide dan belum melakukan surface walking, rute global, atau lompatan antarobjek.
- Mushroom families dan gills lebih berbeda. Hollow Log kini berongga dengan material interior terpisah; sambungan geometri kayu dan pustaka material masih perlu diperluas. Audit visual/game export belum selesai.
- Mid/Low kini menyederhanakan batang/props dan menjaga cakupan kartu berdasarkan proxy sembilan arah; verifikasi siluet pixel-perfect, sudut kamera arbitrer, dan kontrol artistik per kartu masih terbuka.
- Shared wind memiliki hierarki batang/cabang dan gerak kartu dasar; kesesuaian shader dan ekspor animasi ke mesin game belum diuji.
- Normal billboard dasar belum diverifikasi lewat pipeline game; RGB edge dilation sudah tersedia.
- Preset schema 3 portabel menggunakan file resources.blend pendamping; resource harus disertakan bersama JSON.

## Belum diimplementasikan

- Distribusi titik Geometry Nodes live kini tersedia untuk Foliage Surface, Volume, Curve Path dasar, enam pola daun tersusun pada Curve Path, Banana ribbon Curve Path, Ivy Curve Path dengan sulur, Ivy Curve dengan target mesh, serta Ivy utama dan cabang dari plane. Belum mencakup frond pada mesh Surface/Volume atau Tree, Ivy surface-walking untuk sudut/celah atau cabang dari Curve target secara live, dan ornamen otomatis. Jalur instancing lain masih membangun mesh penuh di Python sebelum sumber titik dan buffer dibuat. Progress/cancel untuk operasi berat lain seperti preset, rebind, dan bake Flat di tengah render juga belum ada. Preview density mesh biasa masih memakai proxy yang berbagi mesh sumber; mode kartu terinstans mengurangi mesh sumber dan evaluasi viewport.
- Impostor delapan sudut sudah memilih viewport nonkamera melalui polling arah orbit; tampilan serentak pada beberapa viewport dan pengujian shader game masih terbuka.
- Tekstur starter bunga, ivy, banana/palm, willow, dan acacia serta sebelas gaya solid stylized tersedia; masih perlu lebih banyak varian spesies, kelopak, palet, dan kombinasi material props yang dapat dipilih sebagai preset lengkap.
- Tilt normal khusus dan profil leaflet per-spesies yang lebih kaya; frond droop/taper dasar serta randomisasi bend/valley/tint telah tersedia.
- Uji UI interaktif menyeluruh, undo/redo, deformasi attachment kompleks, kompatibilitas shader game, serta audit topology menyeluruh. Ekspor GLB dasar diuji pada 0.16; append collection lintas file diuji otomatis, tetapi append seluruh scene kompleks belum diaudit interaktif.

Paket ini tidak boleh dilabeli sebagai implementasi penuh rencana sampai daftar di atas dituntaskan dan diuji.
