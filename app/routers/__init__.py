from .auth import router as auth_router
from .users import router as users_router
from .rifiuti import router as rifiuti_router
from .piantumazioni import router as piantumazioni_router
from .censimento import router as censimento_router
from .tronchi import router as tronchi_router
from .strade import router as strade_router

router = auth_router
router.include_router(users_router)
router.include_router(rifiuti_router)
router.include_router(piantumazioni_router)
router.include_router(censimento_router)
router.include_router(tronchi_router)
router.include_router(strade_router)
