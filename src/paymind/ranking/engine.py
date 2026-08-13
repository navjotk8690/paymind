from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from paymind.settings import RankingSettings
@dataclass(frozen=True)
class RankInput:
    option_id:str; payment_type_probability:float; success_probability:float; effective_fee_rate:float; arrival_p50_minutes:float; position:int
@dataclass(frozen=True)
class RankOutput:
    option_id:str; final_score:float; rank:int; cost_score:float; speed_score:float; position_score:float

def rank_options(inputs:Sequence[RankInput], settings:RankingSettings)->list[RankOutput]:
    if not inputs:return []
    fees=[x.effective_fee_rate for x in inputs]; times=[x.arrival_p50_minutes for x in inputs]
    fmin,fmax=min(fees),max(fees); tmin,tmax=min(times),max(times)
    rows=[]
    for x in inputs:
        cost=1.0 if fmax-fmin<=1e-12 else 1-(x.effective_fee_rate-fmin)/(fmax-fmin)
        speed=1.0 if tmax-tmin<=1e-12 else 1-(x.arrival_p50_minutes-tmin)/(tmax-tmin)
        pos=1/max(x.position,1)
        score=settings.payment_type_probability_weight*x.payment_type_probability+settings.success_probability_weight*x.success_probability+settings.cost_weight*cost+settings.speed_weight*speed+settings.position_weight*pos
        rows.append((x,score,cost,speed,pos))
    rows.sort(key=lambda r:(-r[1],r[0].position,r[0].option_id))
    return [RankOutput(r[0].option_id,round(r[1],8),i,round(r[2],8),round(r[3],8),round(r[4],8)) for i,r in enumerate(rows,1)]
