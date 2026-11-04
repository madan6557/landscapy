# Landscapy 0.58.0 — Development Preview

Addon Blender 5.2 untuk eksperimen landscaping stylized. **Ini implementasi awal yang dapat diinstal, bukan penyelesaian seluruh spesifikasi Landscapy.** Rincian pekerjaan yang masih terbuka ada di STATUS.md.

## Instalasi

1. Buka Blender 5.2 → Edit → Preferences → Add-ons → menu → Install from Disk.
2. Pilih `Landscapy-0.58.0-preview.zip`, lalu aktifkan Landscapy. Saat memperbarui versi lama, nonaktifkan addon lama, pasang ZIP baru, lalu restart Blender.
3. Di 3D View, tekan N dan buka tab **Landscapy**.
4. Pilih Create Tree, Foliage, Ivy, Mushroom, atau Prop. Ubah parameter, kemudian tekan **Regenerate**. Foliage dalam mode Live Geometry Cards memperbarui controller dan beberapa parameter langsung.

Untuk mengikuti permukaan: pilih mesh/plane sebelum Create Foliage, atau isi Controller sesudah membuat generator. Auto membedakan mesh tertutup dari permukaan terbuka. Curve Bezier/Poly/NURBS mengikuti hasil evaluasi Blender, termasuk tiap spline terpisah; panjang kurva menentukan density per meter. Volume pada curve dan Path pada mesh mendapat pesan mode yang tidak cocok.

## Tajuk Pine dan pelepah tropis

**Pine** memakai Needle Spray dengan kartu quad besar bertekstur RGBA. Density dan Limit mengalokasikan kartu mulai dari pucuk dan setiap tingkat cabang utama, lalu menambah kartu di bagian luar cabang. **Trunk Clearance** menggeser pangkal kartu menjauh dari batang dan memperpendek pengisi sela antartingkat. **Side Droop** menurunkan sisi kiri dan kanan kartu dari garis tengah. **Lengthwise Arch** menambahkan lengkung sepanjang kartu dan bernilai nol pada preset. **Cluster Length**, **Cluster Width**, dan **Rachis Droop** mengatur bentuk kelompok daun. Ganti gambar atau pakai beberapa gambar berbobot melalui **Texture Slots**. Setelah mengedit bentuk atau slot, tekan **Regenerate**. Density dan Limit dapat diubah langsung pada mode **Live Geometry Cards** dengan **Instanced Card Source** aktif.

**Banana** memakai satu kartu Broad Lamina per helai dengan pangkal mengarah dari pucuk batang semu. **Palm** dan **Coconut** memakai Pinnate Frond, dengan pelepah muda yang lebih tegak dan pelepah tua yang melengkung keluar. Banana Bunch ditambatkan di bagian atas batang semu dan diorientasikan mengikuti gravitasi saat dibuat.

## Hierarki Plant Type (0.55)

Preset tanaman mengisi konfigurasi bertingkat **Plant Type → Trunk Type → Leaf Type → Fruit Type**. Pilihan Trunk Type dibatasi ke arsitektur yang sesuai dengan Plant Type. Leaf Type Tree menempatkan formasi yang direkomendasikan di urutan pertama, sambil tetap membolehkan kombinasi daun kartu lain untuk desain stylized; Fruit Type menawarkan placement yang cocok untuk trunk profile. Pilih Plant Type seperti Mangrove, Pine, Banana, Palm, Coconut, Bonsai Tree, Apple, Mango, atau Grape Vine, lalu tekan **Load Plant Type**. Preset menetapkan bentuk batang/cabang/akar, pola daun, tekstur starter batang, dan rekomendasi susunan buah. Default akar dan keluarga tekstur batang mengikuti profilnya. Tekstur starter hanya diganti otomatis jika slot Bark masih memakai gambar starter Landscapy; image/material buatan pengguna dibiarkan.

Leaf Type memilih formasi di batang atau ranting: Canopy Cluster, Single Card, Opposite Pairs, Alternate, Spiral, Whorled, Needle Spray, Pinnate Frond, atau Broad Lamina. Kartu daun tetap memakai image texture dan dapat diganti lewat **Texture Slots**. Profil batang yang berbeda tetap menentukan tempat rachis/daun tumbuh sehingga Leaf Type mengubah morfologi tanpa mengacak kartu ke seluruh tajuk.

**Fruit** dan **Ornaments** sengaja dipisahkan pada UI, sumber, density, randomisasi, dan output. Keduanya memakai binding permukaan/cabang dan angin yang sama, serta menghindari titik tumbuh yang bertumpuk. Fruit Type mencakup Banana Bunch, Axillary Fruit, Grape Cluster, Coconut Crown Cluster, Hanging Panicle, Raceme, Cauliflorous (batang/cabang tua), Terminal Cluster, Axillary Pods, Conifer Cones, dan Custom Placement. Tombol **Create Matching Fruit Source** menyediakan mesh stylized untuk tiap keluarga; sumbernya dapat diedit atau diganti objek sendiri. Ornament Type tetap menyediakan Flowers, Flower Buds, Seed Pods, serta Custom Object. Tekstur dan material sumber dapat diedit pada objeknya; variasi ukuran, transformasi, warna HSV, opacity, bobot pilihan, dan seed dimiliki tiap kategori.

`demo/plant_catalog_v0550` merangkum semua 19 Plant Type dalam scene editable dan render Eevee; `demo/fruit_hierarchy_v0550` memperlihatkan sepuluh pola placement buah termasuk konifer dan cauliflorous. `demo/integrated_v0540` menyatukan beringin, bonsai, pelepah kelapa, carpet flower/tallgrass, ivy, batu, log, mushroom snap/glow, angin bersama, serta High/Mid/Low/Flat. Flat dibake dengan OptiX. Ini adalah generator bentuk stylized yang memakai aturan morfologi dan bukan simulasi botani seluruh spesies. Buah otomatis memerlukan satu atau beberapa source slot; starter tersedia dari panel Fruit.

## Ivy surface navigation (0.56)

- Seed growth pada mesh kini mengikuti handoff antar-face di sudut tajam dan dapat melintasi celah kecil antar-island mesh. **Gap Bridge (Steps)** membatasi jarak lompatan dalam satuan Growth Step; nilai 0 hanya menerima face yang masih tersambung secara topologi. **Corner Angle Limit** menolak perubahan normal yang lebih tajam dari batasnya.
- Properti navigasi berlaku untuk pertumbuhan Ivy statis yang dibuat ulang. Curve Ivy live tetap mengikuti/proyeksikan guide yang diedit, sehingga opsi ini hanya ditampilkan saat Live Geometry Cards dimatikan.

## Workflow

### Tepi Broad Lamina yang sobek (0.53)

- Pada Leaf Type **Broad Lamina**, panel **Leaf Type Shape** menyediakan **Blade Edge Tear**, **Tear Frequency**, dan **Tear Seed**. Kedua tepi bilah bervariasi secara terpisah; tulang tengah tetap utuh. Nilai nol mengembalikan tepi halus. Seed ini hanya mengubah tepi, bukan sebaran daun, kayu, atau warna.
- Kontrol bekerja live pada Curve, mesh Surface/Volume, serta Tree dengan guide cabang atau mesh tajuk. Generator statis/individual memakai bentuk yang sama setelah Regenerate. UV, alpha, material, dan jumlah face dipertahankan; Build Variants membekukan bentuk sesuai tiap LOD. `demo/blade_tears_v0530` memuat render Eevee dan wireframe. Bentuk yang dibuat adalah takik tepi stylized, belum robekan yang menembus hingga tulang tengah.

### Tree dengan mesh tajuk live (0.52)

- Pilih Tree dan atur **Leaf Type** menjadi Opposite Pairs, Alternate, Spiral, Whorled, Needle Spray, Pinnate Frond, atau Broad Lamina. Masukkan mesh terbuka atau tertutup sebagai **Controller**, lalu aktifkan **Instanced Card Source** dan **Live Geometry Cards**. Auto memilih Surface untuk mesh terbuka dan Volume untuk mesh tertutup; pilihan Volume pada mesh terbuka memberi pesan kesalahan.
- Controller menentukan titik tujuan daun. Geometry Nodes mencari permukaan batang atau cabang terdekat sebagai pangkal setiap rachis, lalu membentuk pelepah menuju titik controller. ID cabang serta koefisien angin dari kayu ikut dibawa ke kartu. Bentuk mesh controller, density, spacing, bobot vertex group mask, ukuran daun, dan angin dapat berubah live. Menambah atau mengganti nama mask, mengganti controller, pola, atau Texture Slots memerlukan **Regenerate**.
- Kayu Tree tetap mesh sumber. Build High/Mid/Low menurunkan detail kayu dan rachis/daun; Flat dibake pada GPU OptiX. `demo/live_tree_mesh_v0520` memuat Tree Surface Pinnate Frond dan Tree Volume Broad Lamina, render Eevee, serta wireframe. Mesh tajuk digunakan sebagai panduan bentuk; pangkal dipilih dari titik kayu terdekat, bukan jaminan ikatan botani pada cabang tertentu.

### Frond live langsung pada Tree (0.50–0.51)

- **Tree Form Preset** mengatur bentuk batang/cabang awal; **Leaf Type** mengatur formasi dedaunan dan dapat diganti secara terpisah. Label **Broad Lamina** (ID lama Banana) membuat satu bilah lebar dengan tulang tengah, **Pinnate Frond** (ID Palm) membuat helai berpasangan sepanjang pelepah, dan **Needle Spray** (ID Conifer) membuat helai pendek sempit. Nama pohon pada ID lama dipertahankan agar preset dan file `.blend` sebelumnya tetap terbaca. Bentuk awal tersedia lewat **Load Leaf Type Shape**. Contohnya, Tree Form Broadleaf dapat memakai Broad Lamina; Tree Form Banana dapat memakai Needle Spray.
- Buat **Tree** dengan Leaf Type Opposite Pairs, Alternate, Spiral, Whorled, Needle Spray, Pinnate Frond, atau Broad Lamina. Aktifkan **Instanced Card Source** dan **Live Geometry Cards** di Distribution, lalu tekan Regenerate. Batang, cabang, dan akar tetap mesh Tree; branch guide ringkas memberi ID cabang serta koefisien angin kepada rachis dan kartu Geometry Nodes pada objek Tree yang sama. Broad Lamina menghasilkan satu bilah ribbon lebar per guide cabang.
- Count, lebar/ukuran daun, sudut, detail rachis, density, warna/opacity, seed, dan angin memperbarui frond tanpa membangun ulang kayu. Mengubah struktur Tree seperti jumlah cabang, tinggi, panjang cabang, Tree Curve controller, atau daftar Texture Slots membutuhkan Regenerate. Curve manual dapat mengarahkan trunk dan cabang; regenerasi mengganti guide frond internal milik Tree.
- Texture Slots RGBA kustom berbobot, ornamen buah/bunga, dan binding cabang tetap tersedia. Build High/Mid/Low/Flat membekukan hasil live, menurunkan detail kayu serta rachis dan segmen bilah Banana untuk Mid/Low, lalu memilih subset kartu sambil melindungi coverage; Flat dibake pada GPU OptiX. Preview, duplikasi, save/reopen, dan append diuji. `demo/live_tree_banana_v0510` berisi scene editable Conifer/Palm/Banana, render Eevee, dan wireframe bilah Banana.
- Tree dengan **mesh canopy controller** untuk Leaf Type berpelepah memakai jalur live 0.52. Canopy Cluster biasa masih memakai distribusi sebelumnya.

### Ivy Curve ke target dengan raycast berarah (0.49)

- Pilih Curve sebagai **Controller** dan mesh sebagai **Target**, lalu buat Ivy dalam mode Path. Di panel **Ivy Growth**, pilih **Curve Surface Projection**: Nearest Surface, Ray Down, atau Custom Ray. Arah ray menggunakan koordinat lokal generator; Custom Ray membuka **Ray Direction (Local)**. Probe membatasi jarak tempel dan Surface Offset menjaga jarak daun/sulur dari permukaan.
- Pilihan metode proyeksi membangun graph berbeda, sehingga ubah metode lalu tekan **Regenerate**. Setelah graph raycast dibuat, edit Curve, mesh target, Probe, Offset, dan Custom Ray Direction bekerja live. Ray yang gagal ditandai `lp_surface_hit=false` dan guide tetap di tempatnya. Arah Custom bernilai nol ditolak dengan pesan yang jelas.
- Proyeksi yang sama tersedia pada generator Ivy statis. Build High/Mid/Low/Flat, gambar RGBA kustom, dan append tetap tersedia. `demo/live_ivy_raycast_v0490` memuat scene editable serta render Eevee dan wireframe untuk arah ke tanah dan ke dinding. Raycast ini belum menelusuri sudut tajam atau menjembatani celah secara otomatis.

### Banana live pada mesh Surface dan Volume (0.48)

- Buat Foliage dengan Controller plane/mesh terbuka untuk Surface atau mesh tertutup untuk Volume. Aktifkan **Live Geometry Cards** dan **Instanced Card Source**, lalu pilih pola **Banana**. Density, Spacing, Limit, bentuk controller, Length, Frond Width, Rachis Segments, droop, bend, twist, dan Valley memperbarui blade serta tangkai tanpa Regenerate setelah graph dibuat. Pergantian controller, pola, atau daftar Texture Slots membutuhkan Regenerate.
- Blade adalah ribbon UV dengan dua quad tiap segmen; tangkainya mesh. Banana mesh memakai radius spline yang valid agar ribbon tidak runtuh menjadi luas nol. Mode Volume memakai **Outward Alignment** untuk memadukan arah acak dengan normal permukaan controller terdekat. Banyak Texture Slots RGBA dapat dipilih berbobot; warna dan opacity tetap dapat diubah.
- Angin mengikuti atribut rachis dan blade: titik pangkal tertahan, sway cluster dan flutter kartu diatur terpisah. Build menghasilkan High/Mid/Low dan Flat GPU OptiX; source live, controller, dan gambar kustom tetap tersedia. `demo/live_banana_mesh_v0480` berisi scene editable, render Eevee, dan wireframe ribbon.

### Frond live pada mesh Surface dan Volume (0.47)

- Buat **Foliage**, pilih Controller mesh, aktifkan **Live Geometry Cards** dan **Instanced Card Source**, lalu pilih pola Opposite, Alternate, Spiral, Whorl, Conifer, atau Palm. Plane/mesh terbuka menggunakan Surface; mesh tertutup dapat memakai Volume. Auto memilih berdasarkan controller.
- **Density** menyebar frond per m² atau m³; **Spacing** mengatur jarak antarpangkal. **Count** mengatur station daun pada tiap frond, **Length** panjang rachis, dan **Limit** membatasi jumlah kartu akhir. Mesh controller, density, spacing, mask, ukuran dan bentuk frond, serta kontrol angin dievaluasi langsung oleh Geometry Nodes. Mengganti pola atau Texture Slots membutuhkan Regenerate.
- Batang rachis adalah mesh, daun adalah kartu RGBA; Texture Slots dapat memakai gambar dan material sendiri, beberapa gambar berbobot, serta variasi warna/opacity. Ornamen otomatis juga dapat disebar pada kartu frond live. Build High/Mid/Low menyederhanakan rachis dan kartu; Flat dibake menggunakan GPU OptiX.
- `demo/live_mesh_fronds_v0470` berisi scene Blender editable, render Eevee Palm Surface dan Conifer Volume, serta wireframe kartu. Banana mesh tersedia mulai 0.48; frond live yang melekat langsung pada Tree masih dalam pengerjaan.

### Ornamen live dan animasi kartu (0.46)

- Foliage dan Ivy dengan **Live Geometry Cards** menerima ornamen otomatis pada Surface, Volume, dan Curve Path. Isi satu atau beberapa **Ornament Source Object**, aktifkan **Enable Ornaments**, lalu tekan **Generate / Update Ornaments**. Individual tidak menjalankan sebaran ornamen otomatis.
- Sebaran ornamen live mengevaluasi geometri kartu pada pose tanpa angin. Density, Limit, dan perubahan bentuk controller mengubah sebaran langsung; ornamen kemudian memakai angin yang sama dengan sumber tanpa menghitung gerak dua kali. Pengaturan ukuran, orientasi, warna, HSV, opacity, dan seed yang sesuai juga bekerja langsung. Mengganti mesh/material sumber, daftar atau bobot slot, dan zona sebaran membutuhkan **Generate / Update Ornaments**. Angka jumlah pada child adalah snapshot saat dibuat; jumlah aktual mengikuti evaluasi live.
- High/Mid/Low mengambil snapshot hasil sebaran dan menyertakan ornamen. Flat membake pose netral dengan GPU OptiX. Source serta controller tetap dapat diedit.
- Mengikuti gerak yang tampak pada video `Blender Project/Ref/stylized tree wind.mp4`, fase ayunan lambat kini dibagi oleh card yang berdekatan atau terikat pada cabang yang sama; fase flutter cepat tetap unik per card. `lp_leaf_wind` menahan pangkal dan memberi gerak lebih besar di ujung. **Cluster Sway**, **Leaf Flutter**, Wind Strength, Speed, Gust, dan Turbulence diatur di panel Wind. Pada card tanpa ID cabang, Cluster Radius menentukan ukuran kelompok fase setelah Regenerate. Video hanya memperlihatkan hasil, bukan node setup asli.
- `demo/live_ornaments_v0460` menyertakan `.blend` editable, render Eevee, dan wireframe. `demo/card_wind_v0460` memperlihatkan foliage carpet dengan ornamen; `demo/card_wind_tree_v0460` memperlihatkan tajuk pohon. Kedua demo angin menyertakan `.blend` dan video Eevee 48 frame/24 fps.

### Growth Wander Ivy plane live (0.44)

- **Growth Wander** kini membengkokkan sulur utama secara bertahap pada mesh/plane Surface live. Pangkal dan ujung guide tetap terikat; cabang tumbuh dari jalur yang sudah dibentuk. Nilai nol menghasilkan guide lurus. Seed yang sama menghasilkan jalur yang sama, dan parameter ini dapat diubah tanpa Regenerate setelah graph dibuat.
- `demo/live_ivy_wander_v0440` berisi `.blend` editable, dua pose render Eevee, dan wireframe. Ini pembentukan guide stylized dengan proyeksi permukaan; sulur belum menelusuri sudut tajam atau menjembatani celah secara otomatis.

### Cabang Ivy plane live (0.43)

- Ivy pada mesh/plane Surface live sekarang membuat sulur utama dan cabang samping. **Side Vines** membatasi jumlah, **Branch Interval** menentukan jarak titik tumbuh, **Branch Angle** dan **Side Vine Length Ratio** mengatur arah serta panjang. **Growth Wander** memberi variasi sudut deterministik per cabang; mengubahnya tidak mengacak Texture Slots. Semua kontrol tersebut langsung mengubah graph setelah Regenerate awal.
- Cabang mengikuti bidang singgung lokal dan masing-masing diproyeksikan ke mesh. Pergantian bentuk, transform, atau shape key controller memperbarui sulur dan kartu. Jika ujung keluar dari Surface Search Distance, bagian itu tetap pada guide dan atribut `lp_surface_hit` menjadi false. Pertumbuhan belum menelusuri sudut tajam atau menjembatani celah secara otomatis.
- Scene `demo/live_ivy_branch_v0430` menyertakan dua pose Eevee, `.blend` editable, dan wireframe kartu/sulur. Build Variants, Flat GPU OptiX, save/reopen, dan append tetap tersedia.

### Ivy pada target mesh dan plane live (0.42)

- Untuk Ivy yang mengikuti **Curve**, isi Controller dengan Curve dan Target dengan mesh. Aktifkan Instanced Card Source serta Live Geometry Cards, pilih Path/Auto, lalu Regenerate sekali. Mode Nearest menempatkan guide pada titik permukaan terdekat; sejak 0.49 mode Ray Down dan Custom Ray juga tersedia. **Surface Search Distance** membatasi jangkauan dan **Surface Offset** memberi jarak; sulur serta daun mengikuti edit Curve, transform/deformasi target, dan parameter live. Titik guide yang gagal menempel tetap pada posisi guide, dengan atribut `lp_surface_hit = false` untuk diagnosis.
- Untuk Ivy dari **plane atau mesh controller**, isi Controller dengan mesh, mode Surface/Auto, dan tentukan Growth Seed, Growth Direction, serta Length. Satu sulur lurus dibentuk dari seed, diarahkan pada bidang singgung permukaan, lalu diproyeksikan. Bila arah awal tegak lurus plane, addon memilih arah tangensial. Edit mesh/shape key, seed, arah, panjang, Growth Step, Surface Offset, dan Search Distance memperbarui hasil live. Growth Step Budget membatasi jumlah sampel per spline.
- Pada 0.42 Ivy plane live memakai satu sulur. Cabang live ditambahkan pada 0.43; navigasi sudut tajam/celah dan kontrol Target terpisah dari Controller mesh masih memakai Regenerate. Mengganti Controller, Target, atau Texture Slots memerlukan Regenerate. Build High/Mid/Low menyederhanakan profil sulur dan resolusi gambar; Flat dibake dengan GPU OptiX.
- Scene editable, dua pose Eevee, dan wireframe tersedia di `demo/live_ivy_target_v0420` serta `demo/live_ivy_plane_v0420`.

### Conifer, Palm, dan Banana Curve Path live (0.41)

- **Conifer** dan **Palm** memakai pola daun berpasangan di sepanjang Curve rachis yang dapat diedit. **Banana** membuat satu blade UV bertekstur per spline Curve, dengan profil tiga titik melintang (dua quad per segmen memanjang) dan tangkai mesh. Gunakan Foliage, Curve controller tanpa bevel, mode Path/Auto, Instanced Card Source, dan Live Geometry Cards; tekan Regenerate setelah memilih pola atau mengganti Texture Slots.
- Banana mengikuti panjang dan lengkung Curve. Rachis Segments menentukan detail blade dan tangkai; Rachis Radial Sides menentukan detail tangkai. Frond Width, Tip Taper, Bare Stem Fraction, Rachis Droop, Leaflet Droop, Bend, Twist, dan Valley memperbarui bentuk live. Satu spline menghasilkan satu blade; Density nol menonaktifkan hasil dan Limit membatasi jumlah spline. Preview menipiskan frond di viewport tanpa mengubah render penuh.
- Texture Slots Banana menerima gambar RGBA pengguna, bobot, ukuran/aspect, pivot, rotasi, dan UV region. Build Mid/Low mengurangi segmen blade serta sisi tangkai, kemudian memperkecil resolusi gambar; Flat memakai OptiX. Galeri editable, render Eevee, dan wireframe ada di `demo/live_frond_advanced_v0410`.
- Bagian Curve Path ini memakai satu guide per spline. Distribusi Conifer/Palm pada mesh tersedia mulai 0.47 dan Banana mesh mulai 0.48. Frond Tree live masih dalam pengerjaan. Bentuk spesies Conifer/Palm masih memerlukan penyempurnaan artistik; contoh menunjukkan struktur live dan teknik kartu.

### Susunan daun Curve Path live (0.40)

- Buat **Foliage** dengan controller Curve tanpa bevel/extrude. Pilih mode **Path** atau **Auto** dan pola **Opposite, Alternate, Spiral, atau Whorl**. Aktifkan **Instanced Card Source** serta **Live Geometry Cards**, lalu tekan **Regenerate** sekali. Setiap spline menjadi tangkai mesh dengan kartu daun yang mengikuti Curve saat diedit. Sumber tetap tanpa face; Curve menentukan panjang dan bentuk tangkai.
- **Density** mengatur station per meter; **Spacing** memberi interval minimum. **Count** membatasi station per spline sebelum Bare Stem Fraction; **Limit** membatasi jumlah kartu akhir, termasuk pasangan dan whorl. Opposite menempatkan dua daun per station, Alternate satu daun berganti sisi, Spiral satu daun berputar, dan Whorl mengikuti Leaves per Whorl.
- Frond Width, Leaflet Width, Tip Taper, Bare Stem Fraction, Leaf Sweep, Rachis Droop, Leaflet Droop, Rachis Radius, Rachis Tip Radius, Rachis Radial Sides, dan Rachis Segments diperbarui langsung. Radius titik pada Curve controller juga memengaruhi ketebalan tangkai. Pangkal daun mewarisi sway tangkai; flutter lokal bernilai nol pada pangkal.
- Texture Slots menerima beberapa gambar RGBA dan bobot. Mengganti gambar/slot atau pola memerlukan **Regenerate**; seed dan parameter live dapat diubah langsung. Build High/Mid/Low mengurangi sisi tangkai menurut rasio, memilih kartu dengan pemeriksaan cakupan alpha, dan memperkecil tekstur Mid/Low. Flat dibake menggunakan GPU OptiX. Preview menipiskan kartu viewport tanpa menghilangkan tangkai.
- Scene editable, render Eevee, dan wireframe empat pola ada di `demo/live_frond_path_v0400`. Conifer, Palm, dan Banana pada Curve Path live ditambahkan di 0.41. Distribusi frond pada mesh Surface/Volume, frond Tree live, dan ornamen otomatis masih memakai generator Regenerate.

### Detail sulur Ivy per versi (0.39)

- **Ivy Growth → Vine Radial Sides** mengatur jumlah sisi dasar sulur. Default High adalah 12 untuk Ivy Path live; perubahan kontrol ini langsung terlihat tanpa Regenerate. Generator Ivy biasa memakai kontrol yang sama saat Regenerate dan juga mempertimbangkan **Solid Mesh Detail**.
- Build Mid/Low dari Ivy Path live sekarang membuat snapshot Geometry Nodes dengan profil sulur lebih sederhana. Default rasio 50%/20% menghasilkan 12 sisi pada High, 6 pada Mid, dan 3 pada Low. Dalam uji contoh, triangle sulur turun 72 → 36 → 18. Pemilihan kartu tetap menjaga cakupan; resolusi gambar Mid/Low tetap turun sesuai **Mid/Low Texture Scale**. Mengubah rasio Build mengubah jumlah sisi hasil sampai batas minimum tiga.
- Graph sumber dan High tidak diubah oleh snapshot Mid/Low. Panjang sulur masih mengikuti titik dan resolusi spline controller; pengurangan segmen sepanjang sulur belum tersedia. Setelah mengubah Vine Radial Sides, jalankan **Build Variants** lagi agar collection keluaran memperbarui geometri.
- Contoh editable, render Eevee, dan render wireframe di `demo/ivy_lod_v0390` memperlihatkan High/Mid/Low berdampingan. Pada contoh itu masing-masing sulur memiliki 1.728/864/432 face; 71 dari 72 kartu daun tetap ada di Mid dan Low karena daun tersebut masih memberi cakupan tampak.

### Ivy Path live (0.38)

- Buat **Ivy**, pilih controller Curve tanpa bevel/extrude, mode **Path** atau **Auto**, lalu aktifkan **Instanced Card Source** dan **Live Geometry Cards**. Tekan **Regenerate** sekali. Satu graph Geometry Nodes membuat sulur mesh dan kartu daun dari tiap spline controller; mengedit Curve langsung memperbarui keduanya. Sumber prosedural tetap tanpa face.
- Density, Leaf Spacing, Leaf Size, Leaf Spread Angle, dan Vine Radius dapat diubah langsung setelah graph dibuat. Texture Slots mendukung beberapa gambar RGBA pengguna, bobot, opacity, UV, dan randomisasi seperti kartu Foliage live. Mengganti gambar, daftar slot, atau rentang variasi memerlukan **Regenerate**. Leaf Spread Angle juga bekerja pada generator Ivy biasa.
- Pangkal daun mengikuti bobot sway sulur; flutter lokal bernilai nol di pangkal. Build High/Mid/Low memilih kartu dari snapshot penuh, menjaga coverage, dan memperkecil resolusi tekstur sesuai pengaturan Build. Pada 0.38, tabung sulur masih memiliki jumlah face yang sama pada High/Mid/Low; 0.39 mengurangi jumlah sisi profilnya. Flat memakai GPU OptiX. Mesh controller, pertumbuhan Ivy pada permukaan, target snap, cabang sulur otomatis, dan ornamen Ivy otomatis masih memakai generator Regenerate.
- Dua scene editable dan render Eevee sebelum/sesudah Curve digeser ada di `demo/live_ivy_v0380`. Controller Curve berfungsi sebagai centerline; Ivy menghasilkan sulur yang terlihat sendiri.

### Kartu Path live (0.37)

- Buat **Foliage**, pilih controller Curve tanpa bevel/extrude, mode **Path** atau **Auto**, lalu aktifkan **Instanced Card Source** dan **Live Geometry Cards**. Tekan **Regenerate** sekali. Kartu mengikuti spline Poly atau Bezier yang diedit, dengan sumbu panjang kartu mengikuti tangent kurva. Beberapa spline dalam satu controller didukung. Density berarti kartu per meter; Spacing menjadi batas interval station di sepanjang tiap spline. Density, Spacing, Limit, dan seed mengubah hasil tanpa Regenerate. Density nol mengosongkan kartu.
- Jarak Euclidean antar kartu dapat lebih kecil daripada Spacing pada tikungan tajam, persilangan, atau setelah Position Jitter. Controller Curve dengan bevel/extrude didiagnosis karena geometry yang dibaca menjadi mesh. Gunakan curve centerline sebagai controller; bila sulur perlu terlihat, buat mesh sulur terpisah yang mengikuti controller, seperti pada scene demo. Mengganti Texture Slots atau rentang bentuk/warna tetap membutuhkan Regenerate.
- `demo/live_path_v0370` berisi dua scene editable dan render Eevee sebelum/sesudah titik Bezier digeser. Kartu serta mesh sulur contoh mengikuti kurva tanpa Regenerate. Build High/Mid/Low memakai snapshot Path live dan Flat memakai bake GPU OptiX. Ini adalah Foliage Path; generator Ivy penuh dengan pertumbuhan bercabang dan ornamen otomatis masih memakai jalur Regenerate.

### Kartu Volume live (0.36)

- Buat generator **Foliage**, pilih controller mesh tertutup, mode **Volume** atau **Auto**, lalu aktifkan **Instanced Card Source** dan **Live Geometry Cards**. Tekan **Regenerate** sekali. Geometry Nodes menempatkan kartu di dalam mesh tanpa menyimpan face kartu pada sumber. Mengubah bentuk atau shape key controller, Density, Spacing, Limit, seed, dan Volume Grid Detail memperbarui hasil tanpa Regenerate. Auto memilih Surface untuk mesh terbuka dan Volume untuk mesh tertutup saat graph dibangun.
- Spacing **0** memakai sebaran acak per m³. Spacing positif memakai grid yang ditipiskan secara deterministik menurut Density. Jarak efektif dapat lebih besar dari nilai Spacing agar jumlah sel tetap terkendali: minimum adalah diagonal bounding box dibagi Volume Grid Detail, dengan batas bawah 0,02 unit. Atribut `lp_distribution_spacing` pada kartu menunjukkan jarak yang dipakai. Grid menjaga jarak minimum sebelum Position Jitter; jumlah akhir dapat berbeda dari target density karena voxelisasi, batas volume, mask, dan Limit. Density mask vertex group diproyeksikan dari permukaan terdekat ke titik interior.
- Controller yang terbuka atau tertutup tetapi tidak memiliki volume mendapat pesan diagnosis. Bila topology controller berubah dari terbuka menjadi tertutup, atau sebaliknya, tekan **Regenerate** agar Auto memilih jalur baru. Distribusi Volume live belum menjalankan pencarian kartu penutup celah tajuk, sehingga density dan orientasi perlu ditinjau dari beberapa sudut. Scene `demo/live_volume_v0360/Landscapy_Live_Volume.blend` menyertakan dua pose shape key dan dua render Eevee; Build Flat tetap memakai GPU OptiX.

### Kartu Surface live (0.35)

- Pada generator **Foliage**, pilih controller mesh terbuka, mode **Surface** atau **Auto**, aktifkan **Instanced Card Source** dan **Live Geometry Cards** di panel Distribution, lalu tekan **Regenerate** sekali. Geometry Nodes menyebar dan membentuk kartu langsung dari controller. Perubahan mesh controller, shape key, Density, Spacing, Limit, seed posisi/warna/tekstur/rotasi/ukuran/bentuk, dan Preview Cards terlihat tanpa Regenerate. Mask vertex group dan normal permukaan diikuti saat dievaluasi. Auto pada volume tertutup memilih Volume; Surface eksplisit dapat digunakan pada mesh tertutup.
- Texture Slots menerima beberapa gambar RGBA pengguna dengan bobot, UV region, aspect, dan pivot masing-masing. Quad serta Valley/Peak dengan bend dan valley acak didukung. Perubahan daftar gambar, rentang randomisasi, warna dasar, atau bentuk kartu masih membutuhkan **Regenerate** untuk membangun ulang graph. Frond tersusun dan ornamen otomatis memakai mode Geometry Nodes Surface Points sebelumnya, yang juga membutuhkan Regenerate.
- Build Variants mengambil snapshot penuh dari graph live, memakai seleksi kartu penjaga cakupan untuk Mid/Low, lalu membake Flat dengan GPU OptiX. Sumber tetap dapat diedit. Angin pada kartu live bereaksi terhadap frame; pose angin nol statis. Scene `demo/live_surface_v0350/Landscapy_Live_Surface.blend` memiliki shape key pada controller di frame 1 dan 40, beserta dua render Eevee. Scene menunjukkan 964→996 face bunga dan tinggi 0,627→1,315 tanpa Regenerate karena luas dan bentuk controller berubah.

### Undo/Redo dan pembatalan Build (0.34)

- Build Variants dari panel sekarang membuat titik Undo sebelum operator modal berjalan. Setelah Build selesai, satu **Undo** menghapus empat hasil versi dan mempertahankan generator sumber; **Redo** mengembalikannya. Perbaikan yang sama berlaku pada Build Collection dengan beberapa generator.
- Uji Blender berjendela tersembunyi di `tests/run_gui_checks.py` memeriksa Create, Regenerate, Build, Build Collection, Undo/Redo, serta Esc selama Build. Esc menghapus hasil parsial dan menyisakan sumber. Runner mengarahkan file sementara dan bake ke folder addon.

### Distribusi Surface lewat Geometry Nodes (0.33)

- Pada generator Foliage dengan controller mesh, aktifkan **Distribution → Geometry Nodes Surface Points**. Mode Surface, atau Auto pada mesh terbuka, akan menyebar titik dengan Geometry Nodes. Density dihitung dari luas controller dalam koordinat dunia; Spacing memakai Poisson, Mask memakai bobot vertex group, dan Limit membatasi jumlah titik. Seed yang sama mengulang sebaran. Curve/Path dan Volume masih memakai jalur distribusi sebelumnya.
- Kartu tetap dibentuk oleh generator Python setelah titik dibaca, sehingga controller perlu **Regenerate** bila berubah. Aktifkan **Instanced Card Source** bila ingin menyimpan hasil sebagai titik dengan kartu yang direalisasikan Geometry Nodes. Kontrol tekstur, randomisasi, Valley, dan Build Variants tetap tersedia. Ini tahap menuju distribusi dan variasi sepenuhnya hidup di node graph, belum tahap akhir.
- Scene editable dan render Eevee bunga serta tallgrass pada mesh melengkung ada di `demo/gn_surface_v0330`. Pembangunan Flat tetap menggunakan GPU OptiX.
- **Build → Flat Bake Directory** menentukan lokasi PNG dan laporan. Path `//` relatif terhadap file `.blend` yang sudah disimpan. Bila file belum disimpan, pilih folder absolut; addon memberi pesan kesalahan alih-alih menulis diam-diam ke C:. Runner pengujian mengarahkan kasus tanpa file tersimpan ke folder `tests/Landscapy_Bakes` dalam addon.

### Akar yang lebih mendatar (0.32)

- Akar otomatis kini mulai agak menjauh dari pusat batang, menyebar lebih cepat di dekat pangkal, merendah ke tanah, dan ujungnya dapat tertanam. Gaya Buttress memiliki pelebaran vertikal di pangkal. Kontrol **Root System** menyediakan Departure, Tip Burial, Buttress Height, serta lokasi, sudut, jangkauan, dan lebar fork.
- Scene editable dan render Eevee perbandingan Surface, Buttress, Exposed tersedia di `demo/roots_v0320`. Aset lama membutuhkan **Regenerate** lalu **Rebuild Variants** agar bentuk baru muncul. Sambungan mesh akar dengan batang masih berupa irisan, belum watertight.

### Kartu bersubdivisi dan daun pisang terinstans (0.31)

- Aktifkan **Distribution → Instanced Card Source** pada Foliage, Tree, atau Ivy lalu tekan **Regenerate**. Quad, Valley/Peak, kartu grid sampai 12 subdivision, dan blade Banana kini menyimpan satu titik per kartu pada sumber. Geometry Nodes mengambil posisi vertex dari buffer titik terpisah dan membentuk kartu lengkap saat evaluasi. UV, material, opacity, atribut angin, dan bentuk hasilnya tetap mengikuti mesh sumber.
- Preview Density menyaring kartu utuh; render serta Build Variants memakai density penuh. Tes mencakup beberapa tekstur, variasi bend/valley, angin, duplikasi, ornamen pada Banana, High/Mid/Low/Flat GPU, append, dan save/reopen. Scene serta render Eevee ada di `demo/instanced_subdivided_v0310`.
- Buffer detail masih menyimpan satu posisi per vertex kartu. Generator sementara tetap menghitung mesh penuh dengan Python sebelum diubah menjadi titik dan buffer; ini belum distribusi titik murni di Geometry Nodes. Mode ini mengurangi face sumber serta biaya evaluasi preview, tetapi tidak menghilangkan seluruh biaya memori kartu bersubdivisi.

### Props kayu tanpa puntiran ring (0.30)

- Stump, batang tumbang, ranting patah, dan prop akar kini memakai orientasi ring yang mengikuti jalur secara kontinu. Kontrol Bend masih mengubah garis tengah sesuai nilai pengguna; permukaan kayu tidak memutar tiba-tiba di antara segmen.
- Scene dan render Eevee enam bentuk kayu ada di `demo/wood_frames_v0300`. Untuk prop lama yang tersimpan dalam `.blend`, pilih prop lalu tekan **Regenerate**; Build Variants lama perlu dibangun ulang.

### Scene demonstrasi terpadu (0.29)

- Buka `demo/integrated_v0290/Landscapy_Integrated_Demo.blend` untuk melihat beringin dengan buah terikat, bonsai dengan Root Curves, kelapa berpelepah, bunga Valley dan tallgrass di mesh terbuka melengkung, ivy mengikuti Curve, batu, jamur yang di-snap, serta hollow log. Collection **Editable Sources** menyimpan generator yang dapat diubah; **Controllers** berisi curve/mesh kontrol. Pilih generator lalu ubah parameter dan tekan **Regenerate**.
- Collection **Landscapy • High/Mid/Low/Flat** berisi empat hasil Build beringin. Hasil Build disembunyikan saat render galeri agar tidak bertumpuk dengan sumber. Atur visibilitas collection sesuai versi yang ingin diperiksa. Flat memakai PNG alpha dari bake GPU OptiX, sedangkan galeri `Landscapy_Integrated_Demo_Eevee.png` dirender dengan Eevee. Detail waktu dan jumlah face tersimpan di `render_report.json`.
- Collection **Editable Sources** dapat di-append ke file Blender baru; relasi ke Root Curves, controller carpet/ivy, target snap, ornamen, dan Wind Controller ikut terbawa. Empat collection hasil Build dapat di-append terpisah. Uji otomatis juga menyimpan dan membuka ulang file hasil append.
- Contoh eksplisit mesh kartu dan wireframe tersedia di `demo/special_foliage_v0100/Landscapy_Flower_Card_Wire.png` dan `demo/lod_v0230/Landscapy_LOD_Wireframe.png`.

### Batang dan kayu tanpa puntiran mesh (0.28)

- Ring pada batang, cabang, dan akar sekarang mempertahankan orientasi sepanjang jalur. Sebelumnya ring dapat berputar mendadak meski batang hampir lurus; ini menyebabkan permukaan dan UV tampak terpuntir. Perbaikan ini juga berlaku pada props kayu yang memakai tube.
- Parameter **Curve** di Shape tetap membengkokkan garis tengah batang sesuai nilai yang dipilih. Nilai nol memberi batang lurus; nilai besar memberi bengkokan seperti pohon pegunungan. Curve controller dan Branch Curves tetap dapat dipakai untuk bentuk manual. Bengkokan yang sengaja dipilih tidak menambah puntiran aksial pada mesh.
- Scene editable serta render Eevee perbandingan empat nilai Curve ada di `demo/trunk_v0280`. Aset `.blend` yang disimpan oleh versi lama perlu **Regenerate** agar geometri batang memakai orientasi baru; hasil Build lama perlu dibangun ulang.
- Perbandingan langsung scene akar 0.26 sebelum dan sesudah **Regenerate** versi 0.29 ada di `demo/tip_v0290`. Cincin yang terlihat dekat pucuk pada gambar lama hilang pada render baru. Pengukuran orientasi ring seluruh batang pada contoh itu turun dari maksimum 68,1° menjadi 0,47°. Enam segmen teratas pada mesh lama tidak memiliki lonjakan sebesar itu, jadi cincin tersebut tidak boleh disimpulkan sebagai puntiran aksial yang terlokalisasi tepat di pucuk.

### Akar dengan curve yang dapat diedit (0.27)

- Pilih generator Tree, buka **Root System**, lalu tekan **Create Editable Root Curves**. Addon membuat satu spline per akar primer saat ini dan memilih **Curves Only**. Pilih objek curve baru, masuk Edit Mode, ubah titik-titiknya, kemudian pilih pohon dan tekan **Regenerate**. Curve panduan disimpan bersama pohon di collection yang sama dan tidak ikut dirender.
- **Root Curves Mode** menyediakan Automatic Only, Auto + Curves, dan Curves Only. Anda juga dapat menyiapkan objek Curve sendiri berisi beberapa spline terbuka dan memasukkannya ke **Root Curves**. Ujung spline yang lebih dekat ke pangkal pohon dipakai sebagai awal akar; spline tertutup ditolak dengan pesan. Setiap spline mengendalikan satu akar, sementara Root Width, Taper, Tip, Flatten, dan Side Forks tetap berlaku.
- Jalur curve dipertahankan sesuai titik yang diedit. **Guide Ground Follow** bernilai nol secara default; naikkan untuk menarik tinggi akar menuju Ground Mesh tanpa mengubah curve sumber. Root Seed dapat mengubah variasi lebar dan fork tanpa menggeser spline manual.
- Contoh scene editable dan render Eevee akar yang diarahkan melewati batu ada di `demo/root_guides_v0270`. Pengarah curve berlaku untuk akar pohon; sambungan akar-batang masih berupa mesh yang berpotongan, belum watertight.

### Root System pohon (0.26)

- Pada generator Tree, buka panel **Root System**. Akar sekarang mengikuti jalur melengkung dari pangkal batang, menipis menuju ujung, dan dapat bercabang. Pilih **Surface** untuk akar dekat tanah, **Buttress** untuk pangkal melebar seperti beringin, atau **Exposed** untuk akar terangkat seperti bonsai. Preset Banyan, Giant, Mountain Bonsai, Twisted Pine, Baobab, Palm, dan Banana memberi konfigurasi awal yang tetap dapat diedit.
- Atur jumlah akar, jangkauan dan variasinya, lebar dan taper, sebaran sudut, wander, tinggi lengkungan, kedalaman tertanam, ketebalan vertikal, jumlah fork, segmen jalur, dan Root Seed. Seed akar terpisah dari cabang/tajuk. Setelah mengubah nilai, tekan **Regenerate**.
- Isi **Ground Mesh** bila akar perlu menyusuri tanah atau batu. **Ground Follow** mencampur ketinggian permukaan dengan ketinggian datar; **Ground Offset** menggeser hasilnya. Pengambilan sampel dilakukan dengan raycast ke bawah. Jika sampel tidak mengenai mesh, panel menampilkan jumlah miss dan sampel tersebut memakai ketinggian lokal.
- High memakai permukaan akar lebih rapat; Build Variants membangun ulang Mid/Low dengan lebih sedikit sisi dan segmen, sementara sumber tetap dapat diedit. Akar terpisah berpotongan dengan batang dan belum menjadi satu mesh watertight. Contoh editable serta render Eevee dekat ada di `demo/roots_v0260`.

### Instansi Quad bertaper/twist dan Valley/Peak (0.25)

- **Instanced Card Source** kini menerima Quad datar maupun bertaper, bengkok, atau twist serta kartu Valley/Peak empat triangle dengan satu vertex tengah. Bentuk, UV, material, ID kartu, dan bobot angin direkonstruksi pada Geometry Nodes dari satu titik per kartu. Tree dan Ivy tetap menyimpan mesh batang/sulur.
- Pelepah Palm dengan leaflet Quad didukung sejak 0.25. Blade Banana dan kartu dengan subdivision lebih dari satu ditambahkan pada 0.31; uji membandingkan vertex, UV, material, dan atribut kartu dengan mesh biasa, termasuk Build dan bake Flat GPU.
- Scene editable dan render Eevee ada di `demo/instanced_shapes_v0250`: carpet bunga Valley menyimpan 211 titik kartu tanpa face sumber; pohon Palm menyimpan 264 titik leaflet dan 1.684 face kayu. Kedua tekstur tetap bisa diganti di Texture Slots.

### Ornamen otomatis pada sumber Quad terinstans (0.24)

- Tree, Ivy, dan Foliage dengan **Instanced Quad Source** kini dapat memakai slot buah, bunga, atau ornamen mesh otomatis. Penempatan dan binding memakai geometri penuh; ketika Preview Density aktif, salinan viewport menipiskan kartu tanpa mengubah topology target ornamen. Sumber render dan Build tetap memakai semua kartu.
- Regenerate memperbarui ornamen dan anchor-nya; slider Preview Cards tidak menggeser buah. Gerak angin batang atau sulur diterapkan lebih dahulu, lalu ornamen mengikuti target sekali. Build menyertakan child ornamen pada High/Mid/Low dan bake Flat. Kombinasi ini memakai lebih banyak memori evaluasi ketika ornamen diaktifkan karena target binding harus tetap lengkap.
- Pengujian otomatis meliputi Tree, Ivy, foliage carpet, perubahan dan toggle preview, angin, Build, duplikasi, serta save/reopen. Dukungan kartu bersubdivisi dan Banana ditambahkan pada 0.31.
- Scene editable dan render Eevee ada di `demo/instanced_ornaments_v0240`: sumber pohon menyimpan 900 kartu daun sebagai titik, 3.000 face kayu, serta 65 buah yang terikat ke tajuk. Gambar dan material sumber buah dapat diganti lalu ornamen dibuat ulang.

### Kartu terinstans untuk Foliage, Tree, dan Ivy (0.23)

- Untuk kartu **Quad**, **Valley/Peak**, atau grid bersubdivisi, aktifkan **Distribution → Instanced Card Source**, lalu **Regenerate**. Foliage, Tree, dan Ivy menyimpan satu titik per kartu; Tree/Ivy tetap menyimpan mesh kayu atau sulur. Geometry Nodes membangun kartu dengan UV, texture slot berbobot, warna, opacity, ID, dan angin. Saat **Preview Density** aktif, node menyaring titik hanya di viewport; render tetap memakai density penuh.
- Mode ini mendukung controller plane/surface/volume/path, Individual, serta attachment manual ke mesh target. Quad bertaper/twist dan Valley/Peak didukung sejak 0.25. Ornamen otomatis tersedia sejak 0.24 untuk generator non-Individual.
- Build Variants merealisasikan High dari sumber lengkap, membentuk Mid/Low sebagai mesh, dan membake Flat dengan density penuh. Mematikan mode lalu Regenerate mengembalikan kartu mesh biasa. Save/reopen dan append collection ke file baru telah diuji. Scene dan render Eevee Tree/Ivy 100% render versus 25% viewport ada di `demo/instanced_wood_v0230`; contoh foliage carpet lama ada di `demo/instances_v0220`.
- Memori mesh sumber dan evaluasi viewport turun karena kartu disimpan sebagai titik; generator sementara masih menghitung kartu penuh sebelum commit dan render/Build tetap merealisasikan geometri penuh. Ornamen otomatis memakai target lengkap untuk binding. Blade Banana dan kartu grid memakai buffer posisi vertex sejak 0.31.

### Perlindungan siluet pada Mid/Low (0.23)

- Kartu yang menutup lubang, menjaga lapisan inti, atau membentuk bagian nyata dari siluet dipertahankan. Kartu yang menonjol hanya dapat dihapus jika hilangnya piksel terlihat sangat kecil pada tiap proyeksi: paling banyak 1% untuk satu kartu dan 2% total per arah. Kartu yang transparan penuh tetap dapat dibuang. Perhitungan memakai alpha/opacity pada sembilan proyeksi 128×128.
- Target rasio atau batas triangle boleh tidak tercapai demi coverage. Laporan Build mencatat piksel siluet yang hilang dan batasnya per arah. Periksa lagi sudut kamera yang penting karena proyeksi terbatas belum menjamin siluet dari setiap arah.
- Scene dan render Eevee pembanding High/Mid/Low/Flat ada di `demo/lod_v0230`. Pada pohon contoh, Mid/Low tetap mempertahankan 2.161 dari 2.200 kartu; kayunya memakai 8.692/2.272/1.244 triangle pada High/Mid/Low dan tekstur 100%/50%/25%.

### Pustaka tekstur solid stylized (0.21)

- Panel **Textures → Solid surfaces** kini menyediakan **Stylized Look** per peran material: sebelas gambar orisinal untuk bark, potongan kayu, batu, jamur, dan moss. Pilih gaya lalu tekan tombol centang di sampingnya dan **Regenerate**. Setiap peran dapat memakai gaya berbeda.
- Gambar pustaka di-pack saat diterapkan, lalu tetap dapat diganti dengan gambar atau material Blender pengguna. Mengubah pilihan menu saja tidak menimpa gambar yang sudah dipasang. Kontrol tint, HSV, mapping, roughness, normal, opacity, dan emission tetap tersedia.
- Build Variants membuat salinan gambar Mid/Low dengan skala resolusi yang dikonfigurasi. Scene editable dan galeri Eevee sembilan contoh ada di `demo/surface_library_v0210`; file pembuat gambar orisinal ada di `tools/create_surface_library.py`.

### Seleksi kartu tajuk Mid/Low (0.20)

- Build Variants tetap mempertahankan High pada kepadatan geometri dan resolusi gambar sumber. Mid/Low membentuk ulang kayu/props pada detail lebih rendah dan membuat salinan semua gambar statis dengan skala resolusi masing-masing (default 50% dan 25% per dimensi).
- Pengurangan kartu Mid/Low kini hanya mempertimbangkan kartu transparan atau kartu yang jelas menonjol di luar area tajuk utama. Kartu pengisi celah dan kartu pembentuk siluet utama dipertahankan. Lapisan terakhir pada piksel inti tidak boleh hilang; pengurangan lapisan kedua dibatasi paling banyak 2% per arah dari sembilan proyeksi alpha.
- Jika rasio atau batas triangle meminta penghapusan kartu penting, Build mempertahankannya dan melaporkan target tidak tercapai. Laporan JSON memuat piksel dua lapis awal dan yang berkurang per arah. Ini perkiraan raster 128×128; periksa tampilan dari sudut kamera penting.
- Contoh pada `demo/lod_v0200` berisi scene `.blend`, galeri Eevee, wireframe, dan laporan JSON. Pohon High/Mid/Low memiliki 8.692/2.272/1.244 triangle kayu serta skala tekstur 100%/50%/25%. Mid/Low mempertahankan 2.161 dari 2.200 kartu karena hanya 39 kartu dekoratif yang lolos syarat pengurangan.

### Create dan Regenerate bertahap (0.19)

- Tombol **Create** dan **Regenerate** di UI memproses kartu dalam batch 128 kartu, menampilkan kemajuan di status/progress Blender, dan menerima **Esc** sebelum mesh baru dikomit. Pembatalan Create membuang objek baru; pembatalan Regenerate mempertahankan mesh sumber, graph cabang, UID, dan status sebelumnya.
- Create/Regenerate yang selesai mendukung satu langkah Undo dan Redo di Blender. Uji Blender berjendela ada di `tests/create_modal_gui_results.json` dan `tests/generate_modal_gui_results.json`; uji pembatalan batch ada di `tests/generate_progress_results.json`.
- API Python/background `landscapy.generate()` tetap sinkron. `landscapy.generate_steps()` dapat dipakai untuk pemrosesan bertahap; menutup iterator sebelum commit membatalkan hasil sementara. Perhitungan controller/tajuk sebelum batch pertama serta binding/ornamen/preview setelah batch terakhir masih berjalan sebagai langkah utuh, sehingga Esc diproses setelah langkah tersebut selesai.

### Pengisian celah tajuk (0.18)

- **Canopy Coverage → Gap Search Samples** menentukan berapa posisi yang dibandingkan untuk setiap kartu pada Tree dan Cloud tanpa mesh controller. Default empat. Generator memilih posisi yang menambah cakupan pada delapan proyeksi samping dan satu proyeksi atas; nilai satu memberi sampling lebih cepat. Lobe pengisi tengah tetap mendapat alokasi khusus saat **Crown Join** digunakan.
- Perkiraan jumlah kartu kini mengukur alpha pada UV region Texture Slots serta Opacity Map, opacity slot, dan rentang opacity kartu. Gambar yang sebagian transparan meminta lebih banyak kartu untuk mencapai target yang sama, tetap tunduk pada **Limit**.
- `demo/canopy_v0180` berisi scene editable dan enam render Eevee transparan dari tiga arah dengan 1 atau 4 kandidat. Pada contoh 1.900 kartu, empat kandidat menambah piksel alfa objek terlihat 5,52%, 4,75%, dan 6,60% pada sudut 0°, 90°, dan 180°. Batangnya sama pada kedua render, sehingga selisih itu berasal dari kartu daun. Ini pengukuran untuk aset contoh, bukan jaminan dari setiap kamera. Pencarian kandidat menambah waktu Generate; nilai 1–8 dapat disesuaikan.

### Batu parametrik (0.17)

- Pilih **Prop**, tentukan Pebble, Boulder, Flat Rock, Shard, atau Stack, lalu tekan **Load Prop Shape Defaults** dan **Regenerate** setelah mengubah parameter. Kelimanya kini memakai bentuk berbeda: kerikil pipih, bongkah, lempeng, pecahan kristalin bersudut, dan tiga lempeng bertumpuk.
- Pada Shape, atur **Rock Proportions**, **Rock Facet Detail**, **Edge Erosion**, jumlah/lebar/kedalaman **Crack**, dan **Moss Coverage**. Detail mesh solid High default lebih tinggi; Mid/Low dibangun ulang dengan jumlah poligon lebih rendah.
- Panel Textures menyediakan peran **Rock**, **Cracks**, dan **Moss**. Ketiganya dapat diberi gambar, normal/roughness/height/opacity/emission map, atau material Blender kustom secara terpisah. Warna bawaan tiap peran ada di Variation. Gambar kustom pada hasil Mid/Low mengikuti **Mid/Low Texture Scale** tanpa mengubah gambar sumber.
- Scene editable dan render Eevee lima bentuk ada di `demo/rocks_v0170`. Uji geometri, bentuk, kontrol, material, Build, dan save/reopen ada di `tests/rock_results.json`.

### Ekspor game dan cakupan LOD (0.16)

- Jalankan **Build Variants**, lalu pilih generator sumber dan klik **Export Game Variants (GLB)** di panel Build. **Export Game Collection** memproses generator Landscapy pada collection yang dipilih. **Game Export Folder** dapat diganti; default `//Landscapy_Exports` relatif terhadap file `.blend`.
- Setiap aset menghasilkan empat GLB terpisah (High, Mid, Low, Flat) dengan gambar terkemas, UV, warna vertex, dan atribut `_LP_*` untuk mask/fase angin, serta satu manifest JSON. Snapshot ekspor membekukan attachment pada frame saat ini dan memakai pose angin netral. Material node kustom yang tidak didukung glTF perlu dicek lagi di game engine.
- Flat delapan arah berisi atlas warna, normal opsional, dan ID tampilan `_LP_IMPOSTOR_VIEW`. Pilihan arah kamera dan shader angin di game engine tetap perlu dibuat sesuai pipeline tujuan.
- Pada Mid/Low, pemilihan kartu memakai alpha dan opacity dari sembilan arah. Mask siluet utama sekarang menutup celah sempit yang terbuka ke tepi tajuk; kartu pengisi celah itu dipertahankan. Kartu tanpa kontribusi pada mask utama, termasuk kartu transparan penuh, menjadi kandidat pengurangan. Laporan Build mencatat piksel siluet utama dan jumlah piksel terlihat sebelum/sesudah per arah.
- Galeri baru di `demo/lod_v0160` berisi `.blend`, render Eevee, wireframe, laporan, serta empat GLB pohon. Pohon contoh mempertahankan 2.140 dari 2.200 kartu pada Mid/Low karena sisanya masih penting bagi cakupan. Target rasio kartu ditandai belum tercapai; kayu tetap turun dari 8.692 menjadi 2.272/1.244 triangle dan tekstur Mid/Low diperkecil menjadi 50%/25% per dimensi.

### Build bertahap dengan kemajuan dan pembatalan (0.15)

- Klik **Build Variants** atau **Build Collection** di panel Build. Blender menampilkan kemajuan High, Mid, Low, dan Flat per generator. Tekan **Esc** untuk membatalkan di antara versi. Bake GPU yang sedang berjalan dapat perlu selesai atau berhenti melalui pembatalan render Blender sebelum Esc diproses.
- Jika dibatalkan sebelum Flat selesai, hasil sementara generator yang sedang diproses dibersihkan; empat versi lama, laporan, dan PNG Flat lama tetap dipertahankan. Pada Build Collection, aset yang sudah selesai sebelum pembatalan tetap memakai hasil barunya.
- Dari Python/background, `landscapy.variants.build()` tetap sinkron. `build_steps()` dan `batch_steps()` dapat dipakai untuk pemrosesan bertahap; `close()` pada iterator yang belum selesai membatalkan aset aktif.

### Props kayu berbeda dan tetap dapat diedit (0.14)

- Pilih **Prop** lalu ubah tipe menjadi Stump, Fallen Trunk, Broken Branch, Root, Vine, atau Hollow Log. Tekan **Load Prop Shape Defaults** untuk ukuran awal yang sesuai, kemudian ubah radius, panjang, bend, dan Solid Mesh Detail. Tombol ini mempertahankan gambar dan material yang sudah dikustomisasi.
- Stump memiliki pangkal melebar dan akar kecil; Fallen Trunk terbaring dengan sisa ranting; Broken Branch memiliki ujung patah; Root menjalar dan bercabang. Vine dapat mengikuti Curve controller atau membentuk sulur spiral jika tanpa controller. Hollow Log benar-benar memiliki rongga dan permukaan bagian dalam.
- Panel **Textures** memberi slot **Wood** untuk kulit, **Cut Wood** untuk bidang potong, dan **Inner Wood** untuk bagian dalam Hollow Log. Bidang potong default memakai pola lingkar tumbuh stylized. Setiap slot dapat diganti gambar, normal/roughness/height/opacity/emission map, atau material Blender sendiri. Bark memakai UV silindris; ujung dan rim memakai UV planar.
- Scene editable dan render Eevee enam bentuk serta close-up rongga tersedia di `demo/wood_props_v0140`. Tujuh pemeriksaan khusus menguji bentuk, edge manifold, UV, pemisahan material, detail High/Mid/Low, curve controller, dan save/reopen.

### Detail kayu, props, dan tekstur tiap versi (0.13)

- **Solid Mesh Detail** pada panel Shape mengatur kepadatan batang/cabang, batu, log, dan jamur. Nilai default High adalah 2: batang mendapat lebih banyak sisi dan sampel sepanjang jalur; cap jamur serta batu mendapat lebih banyak facet. Kartu daun tetap memakai bentuk ringan yang dipilih pengguna.
- Build Variants membentuk ulang geometri solid untuk Mid dan Low dari parameter sumber. Nilai default rasio 0,5 dan 0,2 memberi detail bertingkat pada kayu dan props. High tetap memakai geometri sumber. Parameter dan tekstur sumber tidak berubah.
- **Mid Texture Scale** dan **Low Texture Scale** mengatur panjang dan lebar seluruh gambar statis pada material hasil Build, termasuk gambar dalam node group, peta normal, dan gambar kustom. Default 0,5 dan 0,25; contoh 1024×1024 menjadi 512×512 dan 256×256. Salinan LOD dipack; gambar sumber tidak diubah. Gambar UDIM, sequence, movie, atau viewer dilaporkan sebagai sumber yang belum dapat diresize.
- Pengurangan kartu memakai alpha tekstur dan opacity, lalu memeriksa cakupan dari delapan arah samping dan satu arah atas. Kartu yang mengisi lubang atau memberi dukungan pada siluet utama dipertahankan; kartu tambahan yang menonjol tanpa kontribusi pada cakupan inti dapat dilepas. Rasio kartu dan triangle limit adalah target: jika tidak dapat dipenuhi tanpa mengorbankan cakupan inti, Build berhenti mengurangi kartu dan menandai target belum tercapai pada laporan JSON/status.
- Galeri editable, render Eevee, dan wireframe ada di `demo/lod_v0130`. Contoh pohon memakai 2.200 kartu: High/Mid/Low memiliki 8.692/2.272/1.244 triangle kayu; Mid/Low mempertahankan 1.939 kartu setelah melepas 261 kartu yang menonjol sambil menjaga cakupan inti. Flat tetap dibake dengan GPU OptiX.

Pemeriksaan cakupan memakai proyeksi raster 128×128 per arah sebagai pendekatan. Periksa hasil dari sudut kamera penting untuk aset akhir; ini belum menjamin kesamaan siluet setiap piksel pada resolusi render penuh.

### Angin batang, cabang, dan kartu (0.12)

- Panel **Wind** sekarang memisahkan **Trunk / Stem Sway**, **Branch Bend**, **Cluster Sway**, dan **Leaf Flutter**. Strength, Direction, Speed, Gust, Turbulence, dan Phase tetap tersedia. Shared Wind Controller membawa keempat kontrol tersebut; Asset Response dan Asset Phase Offset tetap dapat diatur per generator.
- Branch Bend memakai ID dan koordinat cabang dari versi 0.11. Setiap cabang anak mewarisi gerakan cabang induknya pada sambungan, lalu menambah bend lokal menuju ujungnya. Kartu daun pada cabang mewarisi gerakan tersebut. Cluster Sway dan Leaf Flutter dibobot oleh `lp_leaf_wind`, sehingga pangkal kartu tetap terikat. Wind nol menghasilkan pose sumber tanpa deformasi.
- Mesh menyimpan `lp_branch_wind_cos`, `lp_branch_wind_sin`, dan `lp_cluster_phase` untuk pemrosesan lebih lanjut. High/Mid/Low mempertahankan atribut ini; Flat tetap memakai sway billboard sederhana. Shader game Unity/Unreal belum termasuk paket.
- Binding manual dan ornamen otomatis membaca mesh target yang sudah dievaluasi. Angin lokal objek terikat default mati, sehingga gerakan target tidak diterapkan dua kali.

Demo `demo/wind_hierarchy_v0120/Landscapy_Hierarchical_Wind_v0120.blend` memuat tiga pohon, satu pengontrol angin, dan buah yang mengikuti cabang panduan. Dua PNG Eevee dan MP4 24 frame (16 fps) ada pada folder yang sama. Pada mesin uji, tiap still sekitar 1–2 detik; 24 frame resolusi 60% sekitar 13 detik sebelum encoding.

### Cabang bertingkat dan spline panduan (0.11)

- Pada Tree → Shape, **Levels** 1–4 membuat cabang anak yang nyata. Seed yang sama menjaga cabang utama tetap pada posisi semula ketika Levels dinaikkan. **Branch Guides** memilih Auto, Hybrid, atau Curve Only. Untuk Hybrid/Curve Only, buat controller Curve dengan spline pertama sebagai batang dan spline berikutnya sebagai cabang utama yang bisa diedit; tekan Regenerate setelah mengubah curve. Curve Only memerlukan sedikitnya satu spline cabang.
- Tiap batang/cabang memiliki atribut mesh `lp_branch_id`, `lp_branch_level`, dan `lp_branch_t`. Metadata jalur disimpan di objek generator sebagai `lp_branch_graph`. ID stabil selama jalur dan urutan spline tidak berubah. Menghapus atau mengurutkan ulang spline dapat mengubah ID cabang manual.
- Untuk buah/bunga hanya pada satu cabang, pilih face cabang atau kartu daunnya dalam Object/Edit Mode, lalu klik **Pick Selected Branch Face** pada Ornaments dan **Generate / Update Ornaments**. Isi **Ornament Branch ID** `-1` untuk seluruh pohon. Jika cabang tidak mempunyai kartu/area eligible pada zona yang dipilih, ornamen tidak dibuat.
- Mesh yang di-**Bind** manual ke pohon menyimpan ID cabang dan koordinat sepanjang jalur selain anchor segitiga. Saat pohon di-Regenerate, addon memindahkan mesh bersama jalur cabang yang diedit lalu membuat ulang anchor permukaannya. Jika cabang itu hilang, status binding menyebut ID yang hilang; pilih target baru dan gunakan Rebind. Mesh luar tetap memakai binding segitiga dan perlu Rebind setelah topology target berubah.

Scene editable dan dua render Eevee ada di `demo/branches_v0110`: perbandingan cabang tingkat satu/empat, dua spline panduan cabang, serta buah yang terikat pada cabang. Scene struktur dan versi bertajuk disimpan terpisah. Render pada mesin uji sekitar 1,2 detik per gambar; waktu berbeda menurut GPU dan resolusi.

### Bunga, willow, dan acacia (0.10)

- Foliage **Flower** memakai satu bunga berbatang; **Flower Cluster** memakai beberapa bunga dalam satu kartu. Memilih pola bunga mengaktifkan kartu Valley/Peak dengan empat triangle secara otomatis. Nilai Valley positif menonjolkan pusat, nilai negatif membuat cekungan; pengguna tetap dapat memilih Quad.
- Preset **Willow** memiliki ranting yang menjuntai dan tajuk vertikal. **Acacia** membentuk tajuk payung yang lebih lebar serta lebih datar. Keduanya memakai tekstur starter daun yang berbeda. Tekstur baru dan tekstur bawaan lain tetap bisa diganti, dicampur dengan banyak Texture Slots berbobot, atau diberi normal/roughness/opacity/height/emission map kustom.
- Perubahan Pattern atau Tree Preset hanya mengganti satu gambar starter yang belum dikustomisasi. Gambar pengguna, multi-slot, serta material override tidak ditimpa. Semua gambar starter dipack ke .blend ketika digunakan agar scene dapat dipindahkan.

Scene `demo/special_foliage_v0100/Landscapy_Special_Foliage_v0100.blend` berisi Willow, Acacia, flower carpet, dan satu kartu bunga Valley yang bisa diedit. Render Eevee dari depan dan samping serta close-up bunga dan wireframe empat triangle ada di folder yang sama.

### Preview density (0.9)

- Pada generator Tree, Foliage, atau Ivy, buka panel Distribution dan aktifkan **Preview Density**. Atur **Preview Cards** untuk menampilkan sebagian kartu utuh secara deterministik di viewport. Nilai 0 hanya memperlihatkan batang/tangkai bila ada; foliage yang hanya berisi kartu menjadi kosong. Nilai 1 kembali menampilkan sumber penuh. Mengubah rasio tidak mengubah seed atau posisi kartu pada sumber.
- Generator sumber tampil sebagai bounding box dan tetap dapat dipilih untuk mengedit pengaturannya. Objek `• Preview` menampilkan kartu dengan Geometry Nodes, tidak bisa dipilih, dan disembunyikan saat render. Sumber penuh tetap dipakai untuk render, attachment, ornamen, dan Build Variants. Regenerate memperbarui proxy; mematikan Preview Density menghapus proxy dan mengembalikan tampilan sumber.
- Preview ini mengurangi geometri yang **ditampilkan** di viewport, tetapi mesh sumber penuh masih berada dalam file dan memori. Distribusi instancing Geometry Nodes untuk scene besar belum tersedia.
- Saat meng-append generator dengan preview ke file baru, sertakan collection yang memuat generator dan objek `• Preview`. Jika hanya generator yang di-append, tekan Regenerate untuk membuat proxy baru.

Scene `demo/preview_v090/Landscapy_Preview_v090.blend` menyimpan generator editable dengan preview aktif serta dua snapshot perbandingan. Render Eevee `Landscapy_Preview_vs_Render.png` menunjukkan 148 dari 650 kartu pada preview dan 650 kartu pada sumber penuh; snapshot diperlukan agar kedua kepadatan terlihat berdampingan dalam satu render.

### Flat delapan arah (0.8)

- Di panel Build, pilih **Flat Mode → Eight Azimuth Views** lalu pilih Resolution per sudut. Default tetap **Single View**. Build Variants membake delapan arah azimuth dari pose netral dengan GPU OptiX dan menyusun warna serta normal opsional dalam atlas 4 kolom × 2 baris. Setiap tile mendapat edge dilation tersendiri agar warna antar-tile tidak bocor.
- Collection Flat berisi satu mesh dengan delapan face, masing-masing menggunakan UV region atlas yang berbeda. Geometry Nodes menampilkan satu face menurut arah scene camera saat render atau Camera View. Saat mengorbit viewport Perspective/Orthographic, arah viewport terakhir yang digerakkan memilih face aktif. Satu mesh hanya mempunyai satu face aktif pada satu waktu, sehingga beberapa viewport dengan arah berbeda tidak bisa menampilkan sudut masing-masing secara bersamaan. Addon harus aktif agar pemilihan sudut otomatis berjalan.
- File `_impostor.json` di `Landscapy_Bakes` mencatat arah lokal, UV region, ukuran tile/atlas, extent, serta konvensi normal. Metadata yang sama disimpan di objek billboard. PNG atlas di-pack ke .blend dan disimpan di disk. Normal memakai tangent space per view: kanan kamera, atas kamera, dan arah ke kamera. Renderer game perlu memilih tile berdasarkan arah kamera serta shader animasi anginnya sendiri.
- Perkiraan memori atlas meningkat dengan kuadrat Resolution. Untuk pengujian awal delapan arah gunakan 256 atau 512; 2048 menghasilkan atlas 8192×4096 dan membutuhkan RAM/GPU lebih besar. Build kini menunjukkan kemajuan dan dapat dibatalkan di antara versi; render GPU aktif tetap berlangsung sebagai satu langkah.
- Source dan Flat bisa di-append sebagai collection ke file baru. Sertakan controller di collection yang sama; gambar kustom dan atlas di-pack dalam .blend. Setelah append, generator tetap dapat diubah dan di-regenerate.

Demo `demo/impostor_v080/Landscapy_Impostor_v080.blend` berisi pohon sumber, atlas warna/normal 512 per view, JSON metadata, dan empat render Eevee dari 0°, 90°, 180°, serta 270°.

### Jamur, snap, dan glow (0.7)

- Pilih mesh target lebih dulu lalu Create Mushroom untuk mengisi Target otomatis, atau pilih Target kemudian. **Snap to Target** mendukung raycast world-down, raycast arah pilihan, dan nearest surface pada mesh target yang sudah dievaluasi. Snap Distance membatasi jangkauan; Offset menjaga jarak dari permukaan. Jika raycast tidak menemukan target, operator menampilkan pesan tanpa memindahkan jamur.
- Batang mengikuti normal permukaan saat di-snap. **Auto Bend** mengarahkan crown ke world-up tanpa mengubah arah batang. **Crown Tilt Random** adalah rentang acak sudut pada arah crown; seed yang sama menghasilkan bentuk sama. Untuk mengikuti perubahan bentuk target setelah snap, gunakan Bind / Rebind to Target.
- Sepuluh keluarga: Button, Dome, Parasol, Bell, Funnel, Morel, Puffball, Coral, Bracket, dan Oyster. Bentuknya parametrik dan stylized. Atur panjang/taper/bending batang, lebar dan ketebalan crown, rim, facets, rings, gills, count cluster, serta spread. Bracket/Oyster berbentuk kipas untuk sisi batang. Coral memiliki cabang dan fork; Morel lebih tinggi dengan permukaan berlekuk sederhana.
- **Glow** menyediakan None, Under, Cap, dan All. Under memakai area bawah crown, Cap bagian atas, All juga membuat batang emissive. Warna/intensitas dapat diatur; semua material stem/cap/gills tetap dapat diganti dengan image atau material Blender sendiri di panel Textures. Material custom penuh menggunakan node pengguna apa adanya.

Scene Eevee `demo/mushrooms_v070/Landscapy_Mushrooms_v070.blend` berisi galeri semua keluarga, dua jamur yang menempel pada log, serta render dari bawah untuk memperlihatkan mask glow. Render galeri sekitar 1,2 detik pada mesin uji.

### Angin dan Build Variants (0.6)

- **Shared Wind Controller:** tombol Create Shared Wind membuat Empty dengan panel pengaturan ketika dipilih. Aset lain dapat memilih Empty tersebut sebagai Wind Controller. Jika **Use Controller Settings** dimatikan, aset memakai pengaturan anginnya sendiri setelah Regenerate. **Asset Response** dan **Asset Phase Offset** tetap per aset, sehingga satu controller dapat menghasilkan gerak berbeda. Kontrol hierarkis terbaru dijelaskan pada bagian 0.12 di atas.
- **Gerak kartu:** atribut `lp_leaf_wind` bernilai nol di pangkal kartu dan meningkat ke ujung. Flutter hanya bekerja pada bagian bebas kartu. Angin nol atau respons nol menghasilkan mesh diam. Binding ornamen mengikuti target tanpa menambah angin lokal secara otomatis.
- **Mid/Low Triangle Limit:** nilai 0 menonaktifkan batas. Jika diisi, Build mengurangi kartu yang tidak dibutuhkan oleh cakupan inti dan ornamen utuh sambil menyederhanakan geometri solid. Laporan JSON mencatat triangle body, ornamen, total, batas, dan apakah batas tercapai. Jika target memerlukan kartu penjaga lubang/siluet, `limit_met: false` dilaporkan.
- **Flat:** PNG alpha dan normal opsional dibake di GPU OptiX. Delapan piksel RGB di sekitar alpha diisi dari tepi opaque, sedangkan alpha dan piksel opaque dipertahankan untuk mengurangi halo saat tekstur difilter. Mode delapan arah tersedia mulai 0.8.

Demo Eevee: `demo/wind_v060/Landscapy_Shared_Wind_v060.blend`, PNG, dan animasi MP4 32 frame (2 detik pada 16 fps). Render still sekitar 1,8 detik dan 32 frame sekitar 17,7 detik pada mesin uji. Angka ini bergantung pada hardware dan scene.

### Frond, kartu daun, dan ivy (0.5)

- **Tree:** Load Tree Preset Palm/Banana/Conifer/Twisted Pine membentuk pelepah bertangkai. Palm/Conifer memiliki leaflet tersusun berpasangan; Banana memakai satu blade panjang bersubdivisi. Tekstur starter yang belum diubah akan mengikuti preset. Slot gambar pengguna, material override, dan peta lain tetap dipertahankan.
- **Foliage:** pilih Palm, Banana, Conifer, Opposite, Alternate, Spiral, atau Whorl. Mode Individual membuat satu pelepah/daun untuk disusun manual. Controller plane/mesh menyebarkannya sesuai density. Panel Frond mengatur jumlah, lebar, taper, bare stem, sudut, droop, ukuran rachis, dan segments. **Limit** menghitung kartu daun akhir; anggaran dibagi antarfrond sebelum daun dibuat.
- **Starter textures:** termasuk Palm Leaflet, Banana Blade, Conifer Leaflet, Broadleaf Single, Ivy Leaf, Flower Single/Cluster, Willow Cluster, dan Acacia Cluster berupa PNG RGBA orisinal. Tombol **Use Starter Leaf Texture** mempertahankan slot lama tetapi memberi weight nol; atur kembali weight untuk mencampur beberapa gambar. Import Texture Images dapat mengisi slot custom. Texture Slot mendukung image, UV region, serta channel normal/roughness/opacity/height/emission dan material sendiri.
- **Ivy Surface:** pilih mesh controller atau target, Mode Surface, tempatkan Growth Seed dekat permukaan, lalu atur Growth Direction, Step, length, branches, wander, offset, dan probe. Raycast/nearest pendek menjaga sulur pada permukaan dan menghentikannya di tepi/gap. Seed pertumbuhan berulang. Mode Path mengikuti curve; jika target mesh juga tersedia, path diproyeksikan ke permukaan. Mode Individual menghasilkan satu kartu ivy. Binding ke target dapat diaktifkan untuk mengikuti deformasi setelah generate.
- **Card shape:** Quad tetap empat vertex. Valley/Peak dasar memakai lima vertex dan empat triangle. Nilai tengah positif sekarang menonjol searah normal face; negatif membentuk cekungan. Card Tip Taper dan rentang acak bend/valley, tint, dan skala per sumbu dapat diubah dengan seed terpisah.
- **Wind:** Direction memutar arah sway pada sumbu lokal generator. Solusi shader angin untuk ekspor game masih pekerjaan terbuka.

Demo Eevee: `demo/fronds_v050/Landscapy_Fronds_v050.blend` berisi tiga preset pohon dan tiga frond Individual, termasuk render kartu tanpa alpha untuk menunjukkan mesh. `demo/ivy_v050/Landscapy_Ivy_v050.blend` menunjukkan mesh melengkung, binding, curve Bezier terpisah, serta ornamen berry. Render PNG ada di folder yang sama. Bake Flat tetap menggunakan GPU OptiX.

### Ornamen dan attachment (0.4)

1. Pilih generator Tree, Foliage, atau Ivy. Mode Individual tidak menjalankan ornamen otomatis.
2. Buka **Ornaments**, aktifkan Enable Ornaments. Pilih **Starter Berry / Starter Flower** atau Add Ornament Source dan pilih mesh sendiri. Sumber tidak dihapus atau diubah oleh generator.
3. Atur weight setiap sumber, density per m² permukaan eligible, Limit, spacing, zona Foliage/Wood/All, dan rentang tinggi. Area dihitung dari face mesh, bukan bagian opaque alpha tekstur.
4. Atur seed distribusi/pilihan/transformasi/warna secara terpisah, ukuran, skala sumbu, pitch/roll/yaw, tint/HSV, serta opacity. **Generate / Update Ornaments** membuat satu child agar tidak menambah ratusan objek ke Outliner.
5. Pada generator live, child mengikuti controller dan density melalui Geometry Nodes; ubah slot, zona, atau sumber lalu tekan Update Ornaments. Pada generator lain, child mengikuti anchor segitiga dan perlu Update/Rebind bila topology target berubah.

Starter sources disimpan tersembunyi dalam `Landscapy • Ornament Sources`. Unhide sumber bila ingin mengedit mesh/materialnya, kemudian Update Ornaments. Material instance merupakan salinan: shader Principled sumber menerima variasi warna/alpha tanpa mengubah sumber. Pada material dengan shader tertanam di node group atau shader non-Principled, gunakan atribut `lp_ornament_color`, `lp_ornament_hsv`, dan `lp_ornament_opacity` di material sendiri; tint otomatis hanya menyisip ke Principled tingkat teratas.

Untuk attachment manual, pilih mesh apa pun (termasuk Individual), buka Landscapy → Target → **Bind / Rebind to Target**. Binding menyimpan indeks triangle, barycentric weights, dan offset dalam frame permukaan. Geometry Nodes mengikuti mesh target yang sudah dievaluasi, termasuk transform, modifier, dan angin. Dependency cycle ditolak.

Jika connectivity topology target berubah, binding dinonaktifkan dan objek kembali ke rest mesh sampai **Rebind**; pemeriksaan juga mendeteksi perubahan dengan jumlah vertex/face sama selama addon aktif. Membuka scene membutuhkan addon aktif untuk pemeriksaan topology. Perubahan jumlah vertex/face juga dijaga oleh node graph. Pada pohon Landscapy, binding manual menyimpan ID cabang dan mencoba memindahkan anchor saat cabang yang sama berubah setelah Regenerate. Binding pada mesh luar tetap berbasis triangle/topology.

**Additional Local Wind** default nonaktif pada objek terikat agar angin target tidak dihitung dua kali. Ubah pilihan tersebut lalu Bind/Rebind atau Regenerate untuk menerapkannya. Detach Binding menghapus ikatan dan mengaktifkan lagi modifier angin lokal yang ada.

High/Mid/Low menyertakan child ornamen dan mengurangi instance ornamen utuh secara deterministik. Child diikat ke badan versi yang bersangkutan, bukan tetap ke badan sumber. Binding eksternal generator dipertahankan; source dengan binding invalid harus di-Rebind sebelum Build. Flat merender badan beserta ornamen pada pose tanpa angin lokal sumber. Build tidak menghentikan animasi target eksternal yang di-attach.

Demo Eevee: `demo/ornaments_v040/Landscapy_Ornaments_v040.blend`, gambar PNG, serta `Landscapy_Ornaments_Wind_v040.mp4` (3 detik, 16 fps, bukan loop seamless).

### Tajuk rapat / Canopy Coverage (0.3)

Mode **Cover Crown** kini menjadi default untuk pohon berdaun cluster dan Foliage dengan pola Cloud tanpa controller. Cluster berbentuk ellipsoid berbatas, saling bertumpang tindih dari ujung cabang menuju bagian tengah tajuk. Sebaran luar lebih merata, bagian dalam tetap diisi, dan kartu diarahkan keluar. Density tidak lagi mengubah geometri percabangan pada mode ini.

- **Cluster Radius:** memperbesar kelompok daun dan pertemuan antarkelompok. Naikkan jika jarak cabang lebar.
- **Crown Coverage:** target jumlah lapisan daun. Tetap dibatasi Density dan Limit.
- **Crown Join:** mengisi ruang di antara kelompok daun cabang pada Broadleaf, Banyan, Giant, dan Baobab. Nol menjaga kelompok terpisah; nilai lebih tinggi menyambungkan massa tajuk. Sampel pengisi diprioritaskan pada bagian dalam agar kartu tidak hanya menumpuk di kulit luar tajuk.
- **Outer Coverage:** pembagian sampel permukaan luar versus isi tajuk.
- **Outward Alignment:** seberapa kuat kartu menghadap sisi luar cluster.
- **Density / Limit:** mengendalikan anggaran kartu. Jika Limit tercapai, status menampilkan pemberitahuan; menaikkan coverage saja tidak akan melampaui Limit.
- **Loose Clusters:** mempertahankan pilihan sebaran Gaussian lama untuk tampilan lebih renggang.

Coverage mempertimbangkan ukuran/aspect kartu, bukan analisis pixel alpha. Tekstur sangat transparan atau kartu kecil mungkin membutuhkan Limit lebih tinggi. Tidak menjamin tajuk menjadi sepenuhnya opaque dari setiap sudut. Mesh controller tetap mengikuti distribusi controller, sedangkan Individual, carpet, ivy, serta struktur Palm/Banana tidak dipaksa menjadi tajuk tertutup.

Preview versi ini memakai **Eevee**. `demo/clustering_v030/` berisi before/after, tiga sudut hasil baru, laporan waktu render, dan file Blender editable.

### Generator dan material

- **Tree:** pilih preset dan tekan Load Tree Preset. Batang/cabang berupa mesh; foliage berupa alpha-textured cards. Preset bentuk tertentu masih berupa pendekatan awal.
- **Foliage:** pilih controller, mode, density, spacing, dan batas jumlah. Mode Individual menghasilkan satu kartu/elemen dasar tanpa controller.
- **Textures:** Import Texture Images menerima beberapa PNG/JPG/TGA/WebP. Atur weight, aspect, size, pivot, rotasi, serta UV region. Gambar di-pack saat diimpor.
- **Semua permukaan dapat dikustomisasi:** Textures → Solid surfaces → Bark/Stem/Wood/Rock/Cap/Gills → aktifkan Customize Surface. Pilih Base Color Image, tint/HSV, roughness, normal, height/bump, opacity, emission, skala/rotasi/offset mapping, serta UV atau Box projection. Klik ikon folder di samping map untuk memuat dan mem-pack file. Tekan Regenerate untuk menerapkan perubahan.
- **Custom Material:** setiap permukaan dan slot foliage dapat memakai material Blender sendiri. Material tersebut digunakan apa adanya, termasuk node groups; regenerate tidak menimpa node pengguna. Material override mengambil alih seluruh shading pada slot tersebut, termasuk variasi warna/alpha bawaan. Jika ingin variasi kartu pada material sendiri, baca atribut `lp_color` dan `lp_opacity`.
- Normal map memakai UVMap dan diasumsikan format tangent-space OpenGL (+Y). Base color, roughness, opacity, height, dan emission mengikuti projection yang dipilih; untuk Box projection gunakan Height/Bump jika ingin detail mengikuti proyeksi Box. Normal map tetap memakai UV. Image untuk data dibuat sebagai salinan Non-Color agar pengaturan albedo yang menggunakan file sama tidak ikut berubah.
- Semua kartu memiliki kontrol map yang sama dengan permukaan padat, selain weight, aspect, pivot, UV atlas, dan randomisasi per kartu. UV batang/cabang dan props kayu kini silindris; bidang potong kayu memakai UV planar. Batu masih memakai proyeksi planar per face. Untuk unwrap produksi khusus, gunakan material sendiri dengan Box projection atau edit mesh hasil Build.
- Saat Customize Surface aktif, Emission Strength/Color pada permukaan menjadi pengaturan glow-nya. Jika tidak aktif, konfigurasi glow generator jamur tetap berlaku.
- **Variation:** seed warna, tekstur, serta orientasi terpisah. Nilai hue berupa offset; saturation/value berupa multiplier.
- **Quad / Valley:** Quad dasar satu face; Valley dasar lima vertex dan empat triangle. Subdivision memungkinkan bending/curl yang lebih halus.
- **Mushroom:** pilih keluarga bentuk, ukuran batang/crown, cluster, serta glow bawah/cap/seluruhnya.
- **Attachments:** Snap menempatkan objek pada titik permukaan terdekat. Bind/Rebind memakai binding barycentric Geometry Nodes seperti dijelaskan di atas. Binding Surface Deform lama diganti ketika menjalankan Bind/Rebind baru.
- **Wind:** gerakan melalui Geometry Nodes dengan mask batang dan ujung kartu. `lp_cluster_phase` mengelompokkan ayunan lambat; `lp_card_phase` membedakan flutter cepat. Empty Shared Wind memiliki panel pengaturan.
- **Build Variants:** membuat High/Mid/Low/Flat, mempertahankan generator sumber. Hasil sengaja disembunyikan agar tidak menumpuk; aktifkan visibility viewport/render pada badan dan child ornamen ketika akan dipakai. Mid/Low menyederhanakan geometri kayu/props, meresize salinan gambar, dan hanya mengurangi kartu yang tidak diperlukan untuk cakupan inti. Ornamen utuh dapat dikurangi; batas triangle bersifat target yang dilaporkan jujur.
- **Flat:** PNG RGBA satu atau delapan sudut, normal map opsional. Normal dibake dalam koordinat kamera yang sesuai tangent basis billboard tiap view. Bake memerlukan OptiX GPU; tidak memakai fallback CPU. Edge dilation RGB tersedia.
- **Save/Load User Preset:** menyimpan JSON schema 4 dan file pendamping `<nama>_resources.blend` yang berisi gambar packed, custom materials, serta mesh sumber Fruit dan Ornaments. Pindahkan kedua file bersama-sama. Preset schema 1–3 tetap dapat dibaca. Sumber yang dimuat disimpan tersembunyi di `Landscapy • Preset Sources`. Preset tree tidak menghapus tekstur kustom ketika bentuk diubah.

## File

- `landscapy/`: source addon dan lima belas tekstur RGBA orisinal.
- `demo/Landscapy_Gallery.blend`: gallery generator yang masih dapat diedit; aktifkan addon sebelum membuka.
- `demo/Landscapy_Gallery.png`: render Cycles OptiX, RTX 4060 Laptop GPU.
- `demo/Landscapy_Custom_Textures_v020.blend` dan `.png`: contoh hasil dengan tekstur kustom pada permukaan pohon, kayu, batu, dan bagian jamur.
- `demo/Landscapy_Bakes/`: contoh billboard dan normal hasil Build Variants.
- `tests/`: pengujian Blender dan laporan JSON.

Tidak ada shader Unity/Unreal. Mesh menyimpan UV, warna, opacity, serta atribut `lp_wind`, `lp_leaf_wind`, `lp_branch_wind_cos`, `lp_branch_wind_sin`, `lp_cluster_phase`, dan `lp_card_phase`. Pemakaian mask tersebut di game engine membutuhkan shader/pipeline tujuan.

Scene 0.1.0 tetap dapat dibuka; pilih generator lalu Regenerate sekali untuk menambahkan daftar permukaan dan UV baru. Konfigurasi tekstur disimpan pada objek, bukan hanya pada material hasil generate. High/Mid/Low menyimpan material yang sudah dikustomisasi; pengurangan LOD menandai kartu melalui atribut `lp_card` sehingga batang yang bertekstur tidak ikut dihapus.

## Batasan operasional

Generator masih menghitung distribusi serta mesh kartu sementara melalui Python. **Instanced Card Source** menyimpan kartu sebagai titik dan Geometry Nodes merealisasikannya; bila dimatikan, sumber memakai mesh penuh. Density tinggi tetap dapat membebani persiapan, render, dan Build. Create, Regenerate, dan Build dari UI memiliki kemajuan serta pembatalan di antara batch atau versi; tahap persiapan dan bake GPU Flat belum dapat dipotong menjadi langkah lebih kecil. Simpan scene sebelum membangun jumlah besar.

Untuk tes/demonstrasi lewat command line, gunakan `python tests/run_blender.py --python tests/nama_skrip.py`, `python tests/run_regression.py`, atau `python tests/run_install_check.py`. Ketiganya mengarahkan TEMP/TMP Blender ke `.temp` di folder addon, sehingga file sementara proses ini tidak memenuhi C:. Arsip pemulihan Landscapy yang perlu disimpan ada di `recovery`.

Jangan menganggap preset bernama sama dengan spesies sebagai model botani akurat. Props kayu sekarang edge manifold dan memiliki material terpisah; sambungan akar/ranting masih berupa mesh yang saling memotong. Uji fungsional tidak menggantikan pemeriksaan visual dan pipeline game.
