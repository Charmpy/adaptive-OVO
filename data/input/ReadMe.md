# Данные

## Предобученные модели

### SAM 2.1

OVO по умолчанию использует **Segment Anything 2.1 (SAM 2.1)**. В проведённых экспериментах использовалась модель с энкодером **Hiera-Large**.

Создайте каталог для хранения checkpoint и загрузите модель:

```bash
cd /<ovo_abs_path>/data/input/

mkdir -p sam_ckpts
cd sam_ckpts

wget https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt
```

После загрузки должна получиться следующая структура:

```text
data/input/sam_ckpts/
└── sam2.1_hiera_large.pt
```

В конфигурации `data/working/configs/ovo.yaml` используются соответствующие параметры:

```yaml
sam:
  sam_ckpt_path: "data/input/sam_ckpts/"
  sam_version: "2.1"
  sam_encoder: "hiera_l"
```

### Модель объединения CLIP-признаков

Для объединения CLIP-признаков используется предобученная модель-предиктор. Загрузите веса по ссылке, указанной в исходном репозитории OVO:

[Скачать веса CLIPs merging weights predictor](https://drive.google.com/file/d/186wZ2mLES_QjUjW8l2DmVmlWDpNl2fSY/view)

Файлы необходимо разместить в каталоге:

```text
/<ovo_abs_path>/data/input/weights_predictor/base/
```

В используемой конфигурации OVO ожидается следующая структура:

```text
data/input/weights_predictor/base/
├── hparams.yaml
└── model.pt
```

Code-маршрут по скачиванию:
```
mkdir -p ~/<ovo_abs_path>/data/input/weights_predictor/base
pip install gdown
gdown 186wZ2mLES_QjUjW8l2DmVmlWDpNl2fSY \
  -O ~/<ovo_abs_path>/data/input/weights_predictor/base/weights.pt
```


> **Примечание:** файл весов должен называться `model.pt`. Если загруженный файл имеет другое имя, его необходимо переименовать.

Соответствующий путь указывается в конфигурации:

```yaml
clip:
  embed_type: learned
  model_card: SigLIP-384
  weights_predictor_path: data/input/weights_predictor/base
```

---

## Датасеты

### Replica

Для экспериментов используется датасет **Replica** с траекториями, подготовленными для NICE-SLAM. Для оценки семантической карты также используется эталонная семантическая разметка (semantic ground truth), предоставляемая вместе с OVO.

Ожидаемая структура данных:

```text
/<ovo_path>/data/input/Datasets/Replica/
├── semantic_gt/
│   ├── office0.txt
│   ├── ...
│   └── room2.txt
│
├── office0/
│   ├── results/
│   └── traj.txt
├── office0_mesh.ply
│
├── ...
│
├── room2/
│   ├── results/
│   └── traj.txt
└── room2_mesh.ply
```

#### Загрузка Replica

В используемой конфигурации сервера датасет Replica загружался через Kaggle из набора `naufalalghifari/nice-slam-replica-dataset`.

Установите Kaggle CLI:

```bash
pip install kaggle
```

Перейдите в каталог датасетов:

```bash
cd /<ovo_abs_path>/
mkdir -p data/input/Datasets
cd data/input/Datasets
```

Загрузите архив:

```bash
kaggle datasets download \
    -d naufalalghifari/nice-slam-replica-dataset
```

Распакуйте его:

```bash
unzip nice-slam-replica-dataset.zip
# rm nice-slam-replica-dataset.zip
```

После распаковки необходимо убедиться, что каталог `Replica` имеет ожидаемую OVO структуру. Например, для сцены `office0`:

```text
data/input/Datasets/Replica/office0/
├── results/
│   ├── frame000000.jpg
│   ├── depth000000.png
│   └── ...
└── traj.txt
```

Также в корне Replica должны находиться mesh-файлы:

```text
data/input/Datasets/Replica/
├── office0_mesh.ply
├── office1_mesh.ply
├── ...
└── room2_mesh.ply
```

#### Подключение семантической разметки

Семантическая GT-разметка находится в репозитории OVO в:

```text
data/input/replica_semantic_gt/
```

Для её подключения создайте символическую ссылку:

```bash
cd /<ovo_abs_path>/data/input/Datasets/Replica

ln -s /<ovo_abs_path>/data/input/replica_semantic_gt semantic_gt
```

Проверить созданную ссылку можно командой:

```bash
ls -l semantic_gt
```

В результате `semantic_gt` должен указывать на:

```text
/<ovo_abs_path>/data/input/replica_semantic_gt
```

---

### ScanNet

Ожидаемая структура датасета ScanNet:

```text
/<ovo_path>/data/input/Datasets/ScanNet/
├── semantic_gt/
│   ├── scene0011_00.txt
│   ├── ...
│   └── scene0704_01.txt
│
├── scannet200_gt/
│   ├── scene0011_00.txt
│   ├── ...
│   └── scene0704_01.txt
│
├── scene0011_00/
│   ├── color/
│   ├── depth/
│   ├── pose/
│   ├── intrinsic/
│   └── scene0011_00_vh_clean_2.labels.ply
│
├── ...
│
└── scene0704_01/
```
