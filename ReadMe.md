# Adaptive-OVO


## Вычислительная среда
Экспериментальная среда была самостоятельно развёрнута и настроена на арендованном удалённом GPU-сервере облачного провайдера Selectel. Параметры системы:

- OS: Ubuntu 24.04.3 LTS (x86_64)
- CPU: 8 vCPU
- RAM: 32 GB
- GPU: NVIDIA GeForce RTX 4090, 24 GB VRAM
- NVIDIA Driver: 580.65.06
- Driver-supported CUDA: 13.0
- Python: 3.11.17
- PyTorch: 2.5.1+cu124
- PyTorch CUDA runtime: 12.4

Для проведения экспериментов на сервере были выполнены развёртывание проекта OVO, настройка Python-окружения и CUDA-зависимостей, установка сторонних модулей, загрузка и конфигурирование нейросетевых моделей, подготовка датасета Replica, а также настройка запуска и сохранения результатов экспериментов.
## Установка

Клонируйте репозиторий с флагом `--recursive`, чтобы также загрузить все используемые подмодули:

```bash
git clone git@github.com:Charmpy/adaptive-OVO.git --recursive
```

Создайте и настройте окружение Conda:

```bash
# Создание Conda-окружения
conda create -n ovo python=3.11
conda activate ovo

# Основные зависимости
conda install pyyaml tqdm psutil wandb plyfile numpy=2.4 matplotlib seaborn opencv=4.11 imageio scipy scikit-learn pandas -c conda-forge

# PyTorch и дополнительные зависимости

pip install torch==2.5.1 torchvision==0.20.1 transformers==4.51.0 open_clip_torch==2.32.0 open3d==0.19.0 huggingface-hub==0.30.1 einops==0.8.1

# SAM2
cd /<ovo_path>/thirdParty/segment-anything-2
pip install -e .

# Perception Encoder
cd /<ovo_path>/thirdParty/perception_models
pip install -e . --no-dependencies
```


## Данные

Инструкции по подготовке и размещению данных приведены в [`data/input/ReadMe.md`](./data/input/ReadMe.md).

## Запуск OVO

Для запуска OVO и вычисления метрик используется скрипт `run_eval.py`.

Поддерживаются следующие аргументы:

- `--dataset_name` — **обязательный параметр**. Используемый датасет: `Replica` или `ScanNet`.
- `--experiment_name` — название каталога, в котором будут сохранены результаты эксперимента: `data/output/<dataset_name>/<experiment_name>`.
- `--run` — запускает OVO для указанных сцен.
- `--segment` — после выполнения OVO использует реконструированную сцену для сегментации эталонного (GT) облака точек.
- `--eval` — после выполнения OVO и сегментации вычисляет итоговые метрики.
- `--dataset_info_file` — файл с информацией о датасете. По умолчанию используется `eval_info.yaml`. Для оценки ScanNet200 необходимо указать `eval_info_200.yaml`.
- `--scenes` — список сцен выбранного датасета, которые необходимо обработать. Если указан `--scenes_list`, данный аргумент игнорируется.
- `--scenes_list` — путь к `.txt`-файлу, содержащему по одному имени сцены в каждой строке. При указании данного параметра `--scenes` игнорируется. Если не указаны ни `--scenes`, ни `--scenes_list`, список сцен загружается из `data/working/config/<dataset_name>/<dataset_info_file>`.

Конфигурация OVO задаётся в файле:

```text
data/working/configs/ovo.yaml
```

Для ускорения моделей SAM можно включить режим компиляции, изменив соответствующие конфигурационные файлы в:

```text
/<conda_path>/envs/ovo/lib/python3.10/site-packages/sam2/configs/sam2.1/
```

### Примеры запуска

Запуск OVO, сегментация GT и вычисление метрик для сцены `office0` датасета Replica:

```bash
python run_eval.py \
    --dataset_name Replica \
    --experiment_name ovo_mapping \
    --run \
    --segment \
    --eval \
    --scenes office0
```

Запуск для полной сцены `scene0011_00` датасета ScanNet:

```bash
python run_eval.py \
    --dataset_name ScanNet \
    --experiment_name ovo_mapping \
    --run \
    --segment \
    --eval \
    --scenes scene0011_00
```
