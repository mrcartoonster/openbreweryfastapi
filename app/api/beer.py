# -*- coding: utf-8 -*-
"""
Location of breweries endpoints.
"""
import sys
from typing import Optional

from environs import Env
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, pagination_params
from fastapi_pagination.ext.tortoise import paginate
from loguru import logger
from tortoise.queryset import QuerySet

from app import crud
from app.crud import FieldEnum, order
from app.desc import brew_type, fmt
from app.log import log
from app.models.tortoise import BrewEnum, Brewery, BrewerySchema

router = APIRouter()


env = Env()
env.read_env()

logger.add(
    sys.stderr,
    format=fmt,
    level="INFO",
)

logger.add(
    "../logs/logged_{time:YYYY-MM-DD at hh:mm:ss A zz}.log",
    rotation="2 days",
)


@router.get(
    "/",
    response_model=Page[BrewerySchema],
    response_model_exclude_none=True,
    dependencies=[Depends(pagination_params)],
)
async def breweries(
    by_city: Optional[str] = Query(
        None,
        description="Filter breweries by city.",
    ),
    by_name: Optional[str] = Query(
        None,
        description="Filter breweries by name.",
    ),
    by_state: Optional[str] = Query(
        None,
        description="Filter breweries by state.",
    ),
    by_postal: Optional[str] = Query(
        None,
        description="Filter breweries by zip code",
        min_length=5,
        max_length=10,
        regex=r"\d{5}(-\d{4})?",
    ),
    by_type: Optional[str] = Query(
        None,
        description=brew_type,
    ),
    sort: Optional[str] = Query(
        None,
        description="Sort the results by one field.",
        regex=r"^(-)?[inbsacplwu]\w.+|(-)?id",
    ),
) -> Page[BrewerySchema]:
    """
    Returns a Page of breweries.
    """
    log.info("Brewery called")
    logger.info("Brewery called")

    # TODO Refactor to make this DRY
    beer = Brewery
    booze = ""

    if any((by_city, by_type, by_name, by_state, by_postal, sort)):

        if by_city:

            log.info(f"The city is {by_city}")

            if by_city.title() not in await beer.all().distinct().values_list(
                "city",
                flat=True,
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"{by_city} is not a city in this dataset.",
                )

            if isinstance(booze, QuerySet) is False:
                booze = beer.filter(
                    city=by_city.title(),
                )

            elif booze.exists():
                booze = booze.filter(city=by_city.title())

            else:
                booze = booze.filter(city=by_city.title())

        if by_type:

            if by_type not in Page(BrewEnum):

                raise HTTPException(
                    status_code=422,
                    detail=f"{by_type} is not a brewery type.",
                )
            log.info(f"{by_type}")

            if isinstance(booze, QuerySet) is False:
                booze = beer.filter(brewery_type=by_type)

            elif booze.exists():
                booze = booze.filter(brewery_type=by_type)
                log.info(f"{booze} is already exists")

            else:
                booze = booze.filter(brewery_type=by_type)

        if by_name:

            if isinstance(booze, QuerySet) is False:
                booze = beer.filter(
                    name__icontains=by_name,
                )
                log.info(f"{booze} doesn't exist.")
                log.info(f"The name is {by_name}")

            elif booze.exists():
                booze = booze.filter(name__icontains=by_name)

            else:
                booze = booze.filter(name__icontains=by_name)

        if by_state:

            if by_state.title() not in await beer.all().distinct().values_list(
                "state",
                flat=True,
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"{by_state} is not a state in the U.S.",
                )

            if isinstance(booze, QuerySet) is False:
                booze = beer.filter(state=by_state.title())

            elif booze.exists():
                booze = booze.filter(state=by_state.title())

            else:
                booze = booze.filter(state=by_state.title())

        if by_postal:

            if isinstance(booze, QuerySet) is False:
                booze = beer.filter(postal_code__icontains=by_postal)

            elif booze.exists():
                booze = booze.filter(postal_code__icontains=by_postal)

            else:
                booze = booze.filter(postal_code__icontains=by_postal)

        if sort:

            if sort.replace("-", "") not in list(FieldEnum):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"'{sort}' not a field. Check BrewerySchema below"
                        " for valid fields."
                    ),
                )

            if isinstance(booze, QuerySet) is False:
                booze = beer.all().order_by(*order(sort))

            elif booze.exists():
                booze = booze.order_by(*order(sort))

            else:
                booze = booze.order_by(*order(sort))

        return await paginate(booze)

    else:
        return await paginate(beer.all())


@router.get(
    "/{id}/",
    response_model=BrewerySchema,
    response_model_exclude_none=True,
)
async def get_breweries(
    id: int = Path(
        ...,
        title="Brewery ID",
    )
) -> BrewerySchema:
    """
    Get a single brewery.
    """
    log.info("Getting Breweries")
    logger.info("Getting Breweries")

    idx = await crud.get(id)

    if not idx:
        raise HTTPException(
            status_code=404,
            detail=f"{id} is not an id of a Brewery in this API.",
        )
    else:
        return idx


@router.get(
    "/search",
    response_model=Page[BrewerySchema],
    response_model_exclude_none=True,
    dependencies=[Depends(pagination_params)],
)
async def brewery_search(
    query: str = Query(
        ...,
        title="Get a Page of breweries with name search.",
    ),
) -> Page[BrewerySchema]:
    """
    General search of brewery with search term.
    """
    log.info("Searching Breweries")
    logger.info("Searching Breweries")

    if query:
        # booze = await crud.search(query)
        booze = Brewery.filter(name__icontains=query)

        if not booze:
            raise HTTPException(
                status_code=404,
                detail=f"'{query}' didn't return anything.",
            )

            log.info(f"Not {booze}")
            logger.info(f"Not {booze}")

        else:
            logger.info("Returning search")
            # return paginate(booze)
            return await paginate(booze)
