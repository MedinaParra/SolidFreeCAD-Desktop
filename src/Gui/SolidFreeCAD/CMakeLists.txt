set(SolidFreeCADGui_SRCS
    SolidActiveSketch.cpp
    SolidActiveSketch.h
    SolidCommandBridge.cpp
    SolidCommandBridge.h
    SolidCommandSearch.cpp
    SolidCommandSearch.h
    SolidDocumentWorkspace.cpp
    SolidDocumentWorkspace.h
    SolidGuiBootstrap.cpp
    SolidGuiBootstrap.h
    SolidGuiManager.cpp
    SolidGuiManager.h
    SolidIconFactory.cpp
    SolidIconFactory.h
    SolidPartDesignMvp.cpp
    SolidPartDesignMvp.h
    SolidPropertyManager.cpp
    SolidPropertyManager.h
    SolidRibbonWidget.cpp
    SolidRibbonWidget.h
    SolidSketchEnhancements.cpp
    SolidSketchEnhancements.h
    SolidTaskOverlayGuard.cpp
    SolidTaskOverlayGuard.h
    SolidWorkspacePolish.cpp
    SolidWorkspacePolish.h
)

target_sources(FreeCADGui PRIVATE ${SolidFreeCADGui_SRCS})

target_include_directories(FreeCADGui PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

source_group("SolidFreeCAD" FILES ${SolidFreeCADGui_SRCS})
