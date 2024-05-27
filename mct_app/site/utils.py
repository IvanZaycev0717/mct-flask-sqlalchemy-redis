from typing import List
from mct_app.site.models import ArticleCard
from config import Months

def get_articles_by_months(article_cards: List[ArticleCard]) -> dict:
    acticles_by_month = {}
    for time, article_id, title in article_cards:
        head = f'{Months(time.month).name} {time.year}'
        if head not in acticles_by_month:
            acticles_by_month[head] = {title: article_id}
        else:
            acticles_by_month[head].update({title: article_id})
    return acticles_by_month


