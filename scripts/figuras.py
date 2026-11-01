"""Reproduce ocho figuras del informe a partir de los CSV del pipeline.

Uso: python3 scripts/figuras.py --results results --output figuras
Requiere: matplotlib, numpy, pandas. No modifica los CSV de resultados.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'figure.dpi': 140, 'savefig.dpi': 170, 'font.size': 9.5,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.18,
})
COLOR = '#126782'
ACCENT = '#D0803A'

def expid(series):
    return series.astype(str).str[-2:]

def save(fig, out, name):
    fig.savefig(out / name, bbox_inches='tight', facecolor='white')
    plt.close(fig)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=Path('results'))
    parser.add_argument('--output', type=Path, default=Path('figuras'))
    args=parser.parse_args()
    out=args.output; out.mkdir(parents=True, exist_ok=True)
    s=pd.read_csv(args.results/'resumen_experimentos.csv').sort_values('experimento')
    i=pd.read_csv(args.results/'resultados_individuales.csv')
    z=pd.read_csv(args.results/'resultados_zonas.csv')
    d=pd.read_csv(args.results/'densidad.csv')
    f=pd.read_csv(args.results/'flujo.csv')
    for df in (s,i,z,d,f): df['exp']=expid(df['experimento'])
    labs=s['exp'].tolist(); xx=np.arange(len(labs))
    fig,ax=plt.subplots(1,2,figsize=(11.5,3.6))
    ax[0].bar(xx,s['velocidad_media_m_s'],yerr=s['desviacion_velocidad_m_s'],color=COLOR,alpha=.85,capsize=3)
    ax[0].set_xticks(xx,labs); ax[0].set_ylabel('Velocidad media (m/s)'); ax[0].set_title('Media ± desviación estándar')
    ax[1].boxplot([i.loc[i.exp==k,'velocidad_media_m_s'].values for k in labs],tick_labels=labs,showfliers=False,patch_artist=True,boxprops={'facecolor':'#DDEEF0'})
    ax[1].set_ylabel('Velocidad individual media (m/s)'); ax[1].set_title('Distribución por peatón')
    fig.tight_layout(); save(fig,out,'figura_01_velocidades.png')

    pg=i.groupby('exp').agg(detencion=('porcentaje_detenido','mean'),eficiencia=('eficiencia','mean')).reindex(labs)
    fig,ax=plt.subplots(1,2,figsize=(11.5,3.6))
    ax[0].bar(labs,pg.detencion,color=ACCENT); ax[0].set_ylabel('Tiempo detenido medio (%)');ax[0].set_title('Detenciones')
    ax[1].bar(labs,pg.eficiencia,color=COLOR);ax[1].set_ylim(0,1.05);ax[1].set_ylabel('Eficiencia media');ax[1].set_title('Rectitud de las trayectorias')
    fig.tight_layout();save(fig,out,'figura_02_detenciones_eficiencia.png')

    fig,ax=plt.subplots(1,2,figsize=(11.5,3.6))
    ax[0].boxplot([i.loc[i.exp==k,'tiempo_total_s'].values for k in labs],tick_labels=labs,showfliers=False)
    ax[0].set_yscale('log');ax[0].set_ylabel('Tiempo de recorrido (s, log)');ax[0].set_title('Variabilidad del tiempo')
    ax[1].boxplot([i.loc[i.exp==k,'eficiencia'].values for k in labs],tick_labels=labs,showfliers=False)
    ax[1].set_ylim(0,1.05);ax[1].set_ylabel('Eficiencia');ax[1].set_title('Variabilidad de la eficiencia')
    fig.tight_layout();save(fig,out,'figura_03_distribuciones.png')

    # Zonas en dirección de marcha, no necesariamente en x creciente.
    sentido=s.set_index('exp')['direccion'].to_dict()
    z['zona_fisica']=z['zona'].str[-1].astype(int)
    z['zona_avance']=z.apply(lambda r: 4-r.zona_fisica if sentido[r.exp]=='right to left' else r.zona_fisica,axis=1)
    fig,ax=plt.subplots(1,2,figsize=(11.5,3.7))
    for zone,c in zip((1,2,3),('#26758F','#D18B44','#659E90')):
        a=z[z.zona_avance==zone].set_index('exp').reindex(labs)
        ax[0].bar(xx+(zone-2)*.24,a.velocidad_media_m_s,width=.23,label=f'Zona {zone}',color=c)
        ax[1].bar(xx+(zone-2)*.24,a.tiempo_medio_s,width=.23,label=f'Zona {zone}',color=c)
    ax[0].set_ylabel('Velocidad media (m/s)');ax[0].set_title('Velocidad por zona de avance')
    ax[1].set_ylabel('Tiempo en zona (s, log)');ax[1].set_yscale('log');ax[1].set_title('Permanencia por zona')
    for a in ax:a.set_xticks(xx,labs)
    ax[0].legend(fontsize=8,frameon=False);fig.tight_layout();save(fig,out,'figura_04_zonas.png')

    x=s['densidad_media_personas_m2'].values;y=s['velocidad_media_m_s'].values
    corr=np.corrcoef(x,y)[0,1]
    fig,ax=plt.subplots(figsize=(6.3,3.8));ax.scatter(x,y,s=66,c=COLOR)
    for _,r in s.iterrows():ax.annotate(r.exp,(r['densidad_media_personas_m2'],r['velocidad_media_m_s']),xytext=(5,5),textcoords='offset points',fontsize=8)
    fit=np.polyfit(x,y,1);interval=np.linspace(x.min(),x.max(),60)
    ax.plot(interval,np.polyval(fit,interval),ls='--',color=ACCENT,label=f'Regresión descriptiva (r={corr:.2f})')
    ax.set_xlabel('Densidad media (personas/m²)');ax.set_ylabel('Velocidad media (m/s)');ax.legend(frameon=False,fontsize=8)
    fig.tight_layout();save(fig,out,'figura_05_velocidad_densidad.png')

    # Agrupación temporal con 0.2 personas/m2; no implica independencia de frames.
    d=d[d.densidad_personas_m2>0].copy()
    d['intervalo']=pd.cut(d.densidad_personas_m2,np.arange(0,2.21,.2),include_lowest=True, right=False)
    grp=d.groupby('intervalo',observed=True).agg(v=('velocidad_media_m_s','mean'),sd=('velocidad_media_m_s','std'),n=('velocidad_media_m_s','size'))
    cent=np.array([k.left+.1 for k in grp.index]);fig,ax=plt.subplots(figsize=(6.3,3.8))
    ax.errorbar(cent,grp.v,yerr=grp.sd,fmt='-o',color=COLOR,capsize=3)
    for xx1, yy1, n in zip(cent,grp.v,grp.n):ax.text(xx1,yy1+.09,f'n={n}',ha='center',fontsize=7)
    ax.set_xlabel('Densidad instantánea (personas/m²)');ax.set_ylabel('Velocidad media por frame (m/s)')
    ax.set_xlim(0,2.2);fig.tight_layout();save(fig,out,'figura_06_densidad_instantanea.png')

    flow=f.groupby('exp').apply(lambda g:pd.Series({'media':g.flujo_personas_s.mean(),'activa':g.loc[g.flujo_personas_s>0,'flujo_personas_s'].mean()}),include_groups=False).reindex(labs)
    fig,ax=plt.subplots(figsize=(9,3.8))
    ax.bar(xx-.2,flow.media,width=.37,color=COLOR,label='Promedio sobre tiempo observado')
    ax.bar(xx+.2,flow.activa,width=.37,color=ACCENT,label='Promedio solo en segundos con cruces')
    ax.set_xticks(xx,labs);ax.set_ylabel('Flujo (personas/s)');ax.set_xlabel('Experimento')
    ax.legend(frameon=False,fontsize=8);fig.tight_layout();save(fig,out,'figura_07_flujo.png')

    fig,ax=plt.subplots(1,2,figsize=(11.5,3.8))
    for axis,k in zip(ax,('01','09')):
        df=d[d.exp==k].copy();df['bin_s']=(df.tiempo_s//5)*5
        series=df.groupby('bin_s').agg(rho=('densidad_personas_m2','mean'),v=('velocidad_media_m_s','mean'))
        axis.plot(series.index,series.rho,color=COLOR,label='Densidad')
        b=axis.twinx();b.plot(series.index,series.v,color=ACCENT,label='Velocidad')
        axis.set_xlabel('Tiempo desde primer frame presente (s)');axis.set_ylabel('Densidad (personas/m²)',color=COLOR)
        b.set_ylabel('Velocidad (m/s)',color=ACCENT);axis.set_title(f'Experimento {k}, medias en intervalos de 5 s')
        axis.grid(True,alpha=.16);b.grid(False)
    fig.tight_layout();save(fig,out,'figura_08_evolucion_temporal.png')
    print(f'Figuras generadas: {len(list(out.glob("figura_*.png")))} en {out}')

if __name__=='__main__': main()
