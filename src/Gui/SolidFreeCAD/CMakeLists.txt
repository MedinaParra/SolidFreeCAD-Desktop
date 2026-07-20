set(SolidFreeCADGui_SRCS
    SolidCommandBridge.cpp
    SolidCommandBridge.h
    SolidCommandSearch.cpp
    SolidCommandSearch.h
    SolidGuiBootstrap.cpp
    SolidGuiBootstrap.h
    SolidGuiManager.cpp
    SolidGuiManager.h
    SolidRibbonWidget.cpp
    SolidRibbonWidget.h
    SolidSketchEnhancements.cpp
    SolidSketchEnhancements.h
)

target_sources(FreeCADGui PRIVATE ${SolidFreeCADGui_SRCS})

target_include_directories(FreeCADGui PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

source_group("SolidFreeCAD" FILES ${SolidFreeCADGui_SRCS})
