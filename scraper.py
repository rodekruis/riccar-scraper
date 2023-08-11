import os
from tqdm import tqdm
import xarray as xr
import click
import urllib.request
GCMs = ['CMCC-CM2-SR5']
Experiments = ['Historical', 'ssp585']
Variables = ['prAdjust', 'tasAdjust', 'tasmaxAdjust', 'tasminAdjust']
YearMin, YearMax = 1961, 2069


def build_url(gcm: str, experiment: str, variable: str, year: int):
    if gcm not in GCMs:
        raise ValueError(f"gcm must be in {GCMs}")
    if experiment not in Experiments:
        raise ValueError(f"experiment must be in {Experiments}")
    if variable not in Variables:
        raise ValueError(f"variable must be in {Variables}")
    if year < YearMin or year > YearMax:
        raise ValueError(f"year must be in {YearMin}-{YearMax}")
    return f"https://www.riccar.org/sites/default/files/nc-files/Downloads/{variable}_MSH-10_{gcm}_{experiment}_" \
           f"r1i1p1f1_SMHI-HCLIM-ALADIN-38_v1_day_regrid_{year}0101-{year}1231_LEV.nc"


def get_files_in_range(directory: str, min: int, max: int):
    files_in_range = []
    for filename in os.listdir(directory):
        basename, ext = os.path.splitext(filename)
        if ext != '.nc':
            continue
        try:
            number = int(basename.split('_')[-2][:4])
        except ValueError:
            continue  # not numeric
        if min <= number <= max:
            # process file
            files_in_range.append(os.path.join(directory, filename))
    return files_in_range


def slice_netcdf(file_path, bbox):
    basename, ext = os.path.splitext(file_path)
    file_path_split = basename + f'_split' + ext
    if os.path.exists(file_path_split):
        os.remove(file_path_split)
    with xr.open_dataset(file_path, engine='h5netcdf') as ds:
        ds.sel(lat=slice(bbox[3], bbox[1]), lon=slice(bbox[0], bbox[2])).to_netcdf(file_path_split)
    os.remove(file_path)
    os.rename(file_path_split, file_path)


@click.command()
@click.option('--dest', default='.', help='output folder')
@click.option('--variable', default='prAdjust', help='variable (short name), can be comma-separated list')
@click.option('--experiment', default='ssp585', help='experiment (short name), can be comma-separated list')
@click.option('--gcm', default='CMCC-CM2-SR5', help='global climate model, can be comma-separated list')
@click.option('--yearmin', default='2023', help='minimum year')
@click.option('--yearmax', default='2023', help='maximum year')
@click.option('--mergeperiods', is_flag=True, default=False, help='merge yearly files into user-defined periods')
@click.option('--periods', default='1961-2001,2021-2061', help='user-defined periods, can be comma-separated list')
@click.option('--slicebbox', is_flag=True, default=False, help='slice files based on bounding box')
@click.option('--bbox', default='(35.4503,33.854127,35.5706,33.922641)', help='bounding box (minx, miny, maxx, maxy)')
def scrape_riccar(dest, variable, experiment, gcm, yearmin, yearmax, mergeperiods, periods, slicebbox, bbox):

    os.makedirs(dest, exist_ok=True)
    years = [int(yearmin)+x for x in range(int(yearmax)-int(yearmin)+1)]
    bbox = [float(i) for i in bbox[1:-1].split(',')]

    print('Downloading files')
    combos = [(gcm_, experiment_, variable_, year_)
              for gcm_ in gcm.split(',')
              for experiment_ in experiment.split(',')
              for variable_ in variable.split(',')
              for year_ in years]
    for combo in tqdm(combos):
        URL = build_url(combo[0], combo[1], combo[2], combo[3])
        filePath = os.path.join(dest, URL.split('/')[-1])
        if os.path.exists(filePath):
            print(f'file already downloaded, skipping: {filePath}')
            continue
        try:
            urllib.request.urlretrieve(URL, filePath)
        except Exception as err:
            print(f'error in creating file: {err}', filePath)
        if slicebbox:
            slice_netcdf(filePath, bbox)

    if mergeperiods:
        periodRanges = periods.split(',')
        print(f'Merging files into {len(periodRanges)} period: {periodRanges}')
        for periodRange in periodRanges:
            yearPeriodMin, yearPeriodMax = periodRange.split('-')
            files = get_files_in_range(dest, int(yearPeriodMin), int(yearPeriodMax))
            mergedFile = xr.DataArray()
            for ix, file in enumerate(files):
                with xr.open_dataset(file, engine='h5netcdf') as ds:
                    if ix == 0:
                        mergedFile = ds.copy()
                    else:
                        mergedFile = xr.merge([mergedFile, ds])
            mergedFileName = f'{variable}_MSH-10_{gcm}_{experiment}_r1i1p1f1_SMHI-HCLIM-ALADIN-' \
                             f'38_v1_day_regrid_{yearPeriodMin}0101-{yearPeriodMax}1231_LEV.nc'
            mergedFilePath = os.path.join(dest, mergedFileName)
            mergedFile.to_netcdf(mergedFilePath)
            if slicebbox:
                slice_netcdf(mergedFilePath, bbox)


if __name__ == "__main__":
    scrape_riccar()