"""Main PySide6 window for BeamCheck."""

from __future__ import annotations

import logging
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QActionGroup, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from beamcheck.core.loads import FullSpanUDL, PointLoad
from beamcheck.core.materials import MATERIAL_PRESETS, Material
from beamcheck.core.models import Beam, BeamType, CalculationInput, CalculationResult, DeflectionCriterion, ProjectInfo
from beamcheck.core.sections import CircularSection, HollowRectangularSection, RectangularSection, SquareHollowSection
from beamcheck.core.solver import solve
from beamcheck.core.units import force_to_si, length_to_si, line_load_to_si, stress_to_si
from beamcheck.gui.plots import beam_schematic, result_diagram
from beamcheck.reporting.formula_trace import build_formula_trace
from beamcheck.reporting.report import export_pdf
from beamcheck.utils.project_io import load_project, save_project
from beamcheck.utils.i18n import LANGUAGES, localized_error, translate


LOGGER = logging.getLogger("beamcheck.gui")


def _spin(value: float, maximum: float = 1_000_000.0, decimals: int = 3) -> QDoubleSpinBox:
    widget = QDoubleSpinBox()
    widget.setRange(0, maximum)
    widget.setDecimals(decimals)
    widget.setValue(value)
    widget.setGroupSeparatorShown(True)
    return widget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("BeamCheck", "BeamCheck")
        saved_language = str(self.settings.value("language", "en"))
        self.language = saved_language if saved_language in LANGUAGES else "en"
        self.current_result: CalculationResult | None = None
        self._canvases: dict[str, FigureCanvasQTAgg] = {}
        self.setWindowTitle(self._t("window_title"))
        self.resize(1280, 820)
        self.setMinimumSize(1050, 700)
        self._build_menu()
        self._build_ui()
        self._apply_style()
        self.reset_form()

    def _t(self, key: str, **values) -> str:
        return translate(self.language, key, **values)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self._t("file"))
        open_action = QAction(self._t("open_project"), self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        save_action = QAction(self._t("save_project"), self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        export_action = QAction(self._t("export_pdf"), self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_report)
        file_menu.addActions([open_action, save_action, export_action])
        settings_menu = self.menuBar().addMenu(self._t("settings"))
        language_menu = settings_menu.addMenu(self._t("language"))
        language_group = QActionGroup(self)
        language_group.setExclusive(True)
        for code, name in LANGUAGES.items():
            action = QAction(name, self, checkable=True)
            action.setChecked(code == self.language)
            action.triggered.connect(lambda checked=False, selected=code: self.change_language(selected))
            language_group.addAction(action)
            language_menu.addAction(action)

    def change_language(self, language: str) -> None:
        if language == self.language or language not in LANGUAGES:
            return
        try:
            current_input = self._make_input()
        except Exception:
            current_input = None
        had_result = self.current_result is not None
        self.language = language
        self.settings.setValue("language", language)
        self.menuBar().clear()
        self._build_menu()
        self._build_ui()
        self._apply_style()
        self.setWindowTitle(self._t("window_title"))
        if current_input is not None:
            self._load_input(current_input)
        else:
            self.reset_form()
        if had_result:
            self.calculate()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_input_panel())
        root.addWidget(self._build_tabs(), 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage(self._t("ready"))

    def _group(self, title: str, layout: QFormLayout | QVBoxLayout) -> QGroupBox:
        group = QGroupBox(title)
        group.setLayout(layout)
        return group

    def _build_input_panel(self) -> QWidget:
        container = QWidget()
        container.setObjectName("inputPanel")
        container.setFixedWidth(365)
        outer = QVBoxLayout(container)
        outer.setContentsMargins(12, 12, 12, 12)
        title = QLabel("BeamCheck")
        title.setObjectName("brand")
        subtitle = QLabel(self._t("subtitle"))
        subtitle.setObjectName("subtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 4, 0, 4)

        project_form = QFormLayout()
        self.project_name = QLineEdit()
        self.calc_title = QLineEdit()
        self.engineer = QLineEdit()
        self.notes = QPlainTextEdit()
        self.notes.setMaximumHeight(58)
        project_form.addRow(self._t("project"), self.project_name)
        project_form.addRow(self._t("title"), self.calc_title)
        project_form.addRow(self._t("engineer"), self.engineer)
        project_form.addRow(self._t("notes"), self.notes)
        form_layout.addWidget(self._group(self._t("project_group"), project_form))

        beam_form = QFormLayout()
        self.beam_type = QComboBox()
        self.beam_type.addItem(self._t("simply_supported"), BeamType.SIMPLY_SUPPORTED.value)
        self.beam_type.addItem(self._t("cantilever"), BeamType.CANTILEVER.value)
        self.beam_length = _spin(4.0, decimals=4)
        self.length_unit = QComboBox()
        self.length_unit.addItems(["m", "mm"])
        length_row = QWidget()
        length_layout = QHBoxLayout(length_row)
        length_layout.setContentsMargins(0, 0, 0, 0)
        length_layout.addWidget(self.beam_length, 1)
        length_layout.addWidget(self.length_unit)
        beam_form.addRow(self._t("support"), self.beam_type)
        beam_form.addRow(self._t("length"), length_row)
        form_layout.addWidget(self._group(self._t("beam_group"), beam_form))

        material_form = QFormLayout()
        self.material_preset = QComboBox()
        for name in MATERIAL_PRESETS:
            self.material_preset.addItem(name, name)
        self.material_preset.addItem(self._t("custom"), "__custom__")
        self.material_preset.currentTextChanged.connect(self._material_changed)
        self.youngs_modulus = _spin(210.0, 10_000, 2)
        self.yield_strength = _spin(355.0, 100_000, 2)
        self.density = _spin(7850.0, 100_000, 1)
        material_form.addRow(self._t("preset"), self.material_preset)
        material_form.addRow("E (GPa)", self.youngs_modulus)
        material_form.addRow("fy (MPa)", self.yield_strength)
        material_form.addRow(self._t("density"), self.density)
        form_layout.addWidget(self._group(self._t("material_group"), material_form))

        section_box = QVBoxLayout()
        self.section_type = QComboBox()
        for key, value in (("rectangular", "rectangular"), ("circular", "circular"), ("rhs", "rhs"), ("shs", "shs")):
            self.section_type.addItem(self._t(key), value)
        self.section_stack = QStackedWidget()
        self.rect_width, self.rect_height = _spin(100), _spin(200)
        self.diameter = _spin(100)
        self.rhs_width, self.rhs_height, self.rhs_thickness = _spin(100), _spin(200), _spin(5)
        self.shs_size, self.shs_thickness = _spin(100), _spin(5)
        for rows in (
            [(self._t("width_mm"), self.rect_width), (self._t("height_mm"), self.rect_height)],
            [(self._t("diameter_mm"), self.diameter)],
            [(self._t("outer_width_mm"), self.rhs_width), (self._t("outer_height_mm"), self.rhs_height), (self._t("wall_mm"), self.rhs_thickness)],
            [(self._t("outer_size_mm"), self.shs_size), (self._t("wall_mm"), self.shs_thickness)],
        ):
            page = QWidget()
            page_form = QFormLayout(page)
            page_form.setContentsMargins(0, 4, 0, 0)
            for label, widget in rows:
                page_form.addRow(label, widget)
            self.section_stack.addWidget(page)
        self.section_type.currentIndexChanged.connect(self.section_stack.setCurrentIndex)
        section_box.addWidget(self.section_type)
        section_box.addWidget(self.section_stack)
        form_layout.addWidget(self._group(self._t("section_group"), section_box))

        loads_layout = QVBoxLayout()
        self.use_point = QCheckBox(self._t("point_load"))
        self.use_point.setChecked(True)
        point_form = QFormLayout()
        self.point_magnitude = _spin(10.0)
        self.point_position = _spin(2.0)
        point_form.addRow("P (kN)", self.point_magnitude)
        point_form.addRow(self._t("position_beam_unit"), self.point_position)
        self.use_udl = QCheckBox(self._t("full_span_udl"))
        self.udl_magnitude = _spin(2.0)
        udl_form = QFormLayout()
        udl_form.addRow("w (kN/m)", self.udl_magnitude)
        loads_layout.addWidget(self.use_point)
        loads_layout.addLayout(point_form)
        loads_layout.addWidget(self.use_udl)
        loads_layout.addLayout(udl_form)
        form_layout.addWidget(self._group(self._t("loads_group"), loads_layout))

        check_form = QFormLayout()
        self.criterion = QComboBox()
        for ratio in (180.0, 250.0, 300.0, 360.0):
            self.criterion.addItem(f"L / {ratio:g}", ratio)
        self.criterion.addItem(self._t("custom"), "custom")
        self.criterion.setCurrentIndex(self.criterion.findData(250.0))
        self.custom_allowable = _spin(10.0)
        self.custom_allowable.setSuffix(" mm")
        self.custom_allowable.setEnabled(False)
        self.criterion.currentIndexChanged.connect(lambda: self.custom_allowable.setEnabled(self.criterion.currentData() == "custom"))
        check_form.addRow(self._t("allowable"), self.criterion)
        check_form.addRow(self._t("custom"), self.custom_allowable)
        form_layout.addWidget(self._group(self._t("deflection_check"), check_form))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(form_widget)
        outer.addWidget(scroll, 1)

        actions = QHBoxLayout()
        self.calculate_button = QPushButton(self._t("calculate"))
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.clicked.connect(self.calculate)
        reset_button = QPushButton(self._t("reset"))
        reset_button.clicked.connect(self.reset_form)
        self.export_button = QPushButton(self._t("export_pdf_button"))
        self.export_button.clicked.connect(self.export_report)
        self.export_button.setEnabled(False)
        actions.addWidget(reset_button)
        actions.addWidget(self.calculate_button)
        actions.addWidget(self.export_button)
        outer.addLayout(actions)
        return container

    def _build_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()
        self.plot_hosts: dict[str, QVBoxLayout] = {}
        for key, title_key in (("beam", "tab_beam"), ("results", "tab_results"), ("shear", "tab_shear"), ("moment", "tab_moment"), ("deflection", "tab_deflection"), ("calculation", "tab_calculation")):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(18, 18, 18, 18)
            if key in {"beam", "shear", "moment", "deflection"}:
                placeholder = QLabel(self._t("plot_placeholder"))
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setObjectName("placeholder")
                layout.addWidget(placeholder)
                self.plot_hosts[key] = layout
            elif key == "results":
                self.results_grid = QGridLayout()
                layout.addLayout(self.results_grid)
                layout.addStretch()
            else:
                self.formula_text = QPlainTextEdit()
                self.formula_text.setReadOnly(True)
                self.formula_text.setFont(QFont("Consolas", 10))
                self.formula_text.setPlaceholderText(self._t("formula_placeholder"))
                layout.addWidget(self.formula_text)
            self.tabs.addTab(page, self._t(title_key))
        return self.tabs

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f1f5f9; }
            QWidget#inputPanel { background: #ffffff; border-right: 1px solid #cbd5e1; }
            QLabel#brand { color: #183153; font-size: 25px; font-weight: 700; }
            QLabel#subtitle { color: #64748b; margin-bottom: 5px; }
            QLabel#placeholder { color: #64748b; font-size: 14px; }
            QGroupBox { font-weight: 600; color: #183153; border: 1px solid #dbe4ee; border-radius: 6px; margin-top: 10px; padding: 8px 5px 5px 5px; }
            QGroupBox::title { subcontrol-origin: margin; left: 9px; padding: 0 4px; }
            QLineEdit, QPlainTextEdit, QDoubleSpinBox, QComboBox { border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; background: white; }
            QPushButton { padding: 7px 10px; border: 1px solid #94a3b8; border-radius: 5px; background: #f8fafc; }
            QPushButton:hover { background: #e2e8f0; }
            QPushButton#primaryButton { background: #2563eb; color: white; border-color: #2563eb; font-weight: 600; }
            QTabWidget::pane { border: 0; background: white; }
            QTabBar::tab { padding: 10px 17px; background: #e2e8f0; color: #334155; }
            QTabBar::tab:selected { background: white; color: #183153; font-weight: 600; }
            """
        )

    def _material_changed(self, _displayed_name: str) -> None:
        preset = self.material_preset.currentData()
        if preset in MATERIAL_PRESETS:
            material = MATERIAL_PRESETS[preset]
            self.youngs_modulus.setValue(material.youngs_modulus / 1e9)
            self.yield_strength.setValue(material.yield_strength / 1e6)
            self.density.setValue(material.density)

    def _make_input(self) -> CalculationInput:
        beam_unit = self.length_unit.currentText()
        length = length_to_si(self.beam_length.value(), beam_unit)
        material = Material(
            self.material_preset.currentData() if self.material_preset.currentData() != "__custom__" else self._t("custom_material"),
            stress_to_si(self.youngs_modulus.value(), "GPa"),
            stress_to_si(self.yield_strength.value(), "MPa"),
            self.density.value(),
        )
        section_type = self.section_type.currentData()
        if section_type == "rectangular":
            section = RectangularSection(length_to_si(self.rect_width.value(), "mm"), length_to_si(self.rect_height.value(), "mm"))
        elif section_type == "circular":
            section = CircularSection(length_to_si(self.diameter.value(), "mm"))
        elif section_type == "rhs":
            section = HollowRectangularSection(length_to_si(self.rhs_width.value(), "mm"), length_to_si(self.rhs_height.value(), "mm"), length_to_si(self.rhs_thickness.value(), "mm"))
        else:
            size = length_to_si(self.shs_size.value(), "mm")
            section = SquareHollowSection(size, size, length_to_si(self.shs_thickness.value(), "mm"))

        loads = []
        if self.use_point.isChecked():
            loads.append(PointLoad(force_to_si(self.point_magnitude.value(), "kN"), length_to_si(self.point_position.value(), beam_unit)))
        if self.use_udl.isChecked():
            loads.append(FullSpanUDL(line_load_to_si(self.udl_magnitude.value(), "kN/m")))

        criterion_value = self.criterion.currentData()
        criterion = DeflectionCriterion(custom_allowable=length_to_si(self.custom_allowable.value(), "mm"), ratio=None) if criterion_value == "custom" else DeflectionCriterion(ratio=float(criterion_value))
        return CalculationInput(
            Beam(BeamType(self.beam_type.currentData()), length),
            material,
            section,
            tuple(loads),
            criterion,
            ProjectInfo(self.project_name.text().strip() or self._t("untitled_project"), self.calc_title.text().strip() or self._t("beam_calculation"), self.engineer.text().strip(), self.notes.toPlainText().strip()),
        )

    def calculate(self) -> None:
        try:
            result = solve(self._make_input())
        except ValueError as exc:
            LOGGER.warning("Validation failed: %s", exc)
            QMessageBox.warning(self, self._t("check_input"), localized_error(str(exc), self.language))
            return
        except Exception as exc:
            LOGGER.exception("Unexpected calculation failure")
            QMessageBox.critical(self, self._t("calculation_failed"), self._t("unexpected_error", error=exc))
            return
        self.current_result = result
        self._show_result(result)
        self.export_button.setEnabled(True)
        self.statusBar().showMessage(self._t("calculation_complete"))
        LOGGER.info("Calculation completed for %s", result.input.beam.beam_type.value)

    def _set_figure(self, key: str, figure) -> None:
        layout = self.plot_hosts[key]
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        canvas = FigureCanvasQTAgg(figure)
        layout.addWidget(canvas)
        canvas.draw()
        self._canvases[key] = canvas

    def _result_card(self, title: str, value: str, status: bool | None = None) -> QFrame:
        card = QFrame()
        card.setStyleSheet("QFrame { background: #f8fafc; border: 1px solid #dbe4ee; border-radius: 8px; padding: 12px; }")
        layout = QVBoxLayout(card)
        heading = QLabel(title)
        heading.setStyleSheet("color: #64748b; font-size: 12px; border: 0;")
        number = QLabel(value)
        color = "#15803d" if status is True else "#b91c1c" if status is False else "#183153"
        number.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700; border: 0;")
        layout.addWidget(heading)
        layout.addWidget(number)
        return card

    def _show_result(self, result: CalculationResult) -> None:
        self._set_figure("beam", beam_schematic(result, self.language))
        self._set_figure("shear", result_diagram(result, "shear", self.language))
        self._set_figure("moment", result_diagram(result, "moment", self.language))
        self._set_figure("deflection", result_diagram(result, "deflection", self.language))
        while self.results_grid.count():
            item = self.results_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        values = [
            (self._t("maximum_shear"), f"{result.max_abs_shear / 1000:.4g} kN", None),
            (self._t("maximum_moment"), f"{result.max_abs_moment / 1000:.4g} kN·m", None),
            (self._t("bending_stress"), f"{result.max_bending_stress / 1e6:.4g} MPa", result.stress_check.passes),
            (self._t("factor_of_safety"), f"{result.factor_of_safety:.4g}", result.stress_check.passes),
            (self._t("maximum_deflection"), f"{result.max_deflection * 1000:.4g} mm", result.deflection_check.passes),
            (self._t("deflection_check"), self._t("pass") if result.deflection_check.passes else self._t("fail"), result.deflection_check.passes),
        ]
        for index, data in enumerate(values):
            self.results_grid.addWidget(self._result_card(*data), index // 2, index % 2)
        self.formula_text.setPlainText(build_formula_trace(result, self.language))

    def export_report(self) -> None:
        if self.current_result is None:
            QMessageBox.information(self, self._t("calculate_first"), self._t("calculate_before_export"))
            return
        default_name = self._t("report_filename", project=self.current_result.input.project.project_name or "BeamCheck")
        filename, _ = QFileDialog.getSaveFileName(self, self._t("export_report_dialog"), str(Path.cwd() / default_name), self._t("pdf_files"))
        if not filename:
            return
        try:
            export_pdf(self.current_result, filename, self.language)
        except Exception as exc:
            LOGGER.exception("PDF export failed")
            QMessageBox.critical(self, self._t("export_failed"), self._t("pdf_failed", error=exc))
            return
        self.statusBar().showMessage(self._t("report_exported", path=filename))
        LOGGER.info("PDF report exported")

    def save_project(self) -> None:
        try:
            case = self._make_input()
            case.validate()
        except ValueError as exc:
            QMessageBox.warning(self, self._t("check_input"), localized_error(str(exc), self.language))
            return
        filename, _ = QFileDialog.getSaveFileName(self, self._t("save_project_dialog"), str(Path.cwd() / "project.beamcheck.json"), self._t("project_files"))
        if filename:
            save_project(case, filename)
            self.statusBar().showMessage(self._t("project_saved", path=filename))

    def open_project(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, self._t("open_project_dialog"), str(Path.cwd()), self._t("project_files") + ";;JSON (*.json)")
        if not filename:
            return
        try:
            case = load_project(filename)
            self._load_input(case)
            self.current_result = None
            self.export_button.setEnabled(False)
            self.statusBar().showMessage(self._t("project_loaded"))
        except ValueError as exc:
            QMessageBox.warning(self, self._t("open_failed"), localized_error(str(exc), self.language))

    def _load_input(self, case: CalculationInput) -> None:
        self.project_name.setText(case.project.project_name)
        self.calc_title.setText(case.project.calculation_title)
        self.engineer.setText(case.project.engineer)
        self.notes.setPlainText(case.project.notes)
        self.beam_type.setCurrentIndex(self.beam_type.findData(case.beam.beam_type.value))
        self.length_unit.setCurrentText("m")
        self.beam_length.setValue(case.beam.length)
        preset_key = next((key for key, material in MATERIAL_PRESETS.items() if material == case.material), "__custom__")
        self.material_preset.setCurrentIndex(self.material_preset.findData(preset_key))
        self.youngs_modulus.setValue(case.material.youngs_modulus / 1e9)
        self.yield_strength.setValue(case.material.yield_strength / 1e6)
        self.density.setValue(case.material.density)
        section = case.section
        if isinstance(section, SquareHollowSection):
            self.section_type.setCurrentIndex(self.section_type.findData("shs"))
            self.shs_size.setValue(section.outer_width * 1000)
            self.shs_thickness.setValue(section.wall_thickness * 1000)
        elif isinstance(section, HollowRectangularSection):
            self.section_type.setCurrentIndex(self.section_type.findData("rhs"))
            self.rhs_width.setValue(section.outer_width * 1000)
            self.rhs_height.setValue(section.outer_height * 1000)
            self.rhs_thickness.setValue(section.wall_thickness * 1000)
        elif isinstance(section, RectangularSection):
            self.section_type.setCurrentIndex(self.section_type.findData("rectangular"))
            self.rect_width.setValue(section.width * 1000)
            self.rect_height.setValue(section.height * 1000)
        else:
            self.section_type.setCurrentIndex(self.section_type.findData("circular"))
            self.diameter.setValue(section.diameter * 1000)
        point = next((load for load in case.loads if isinstance(load, PointLoad)), None)
        udl = next((load for load in case.loads if isinstance(load, FullSpanUDL)), None)
        self.use_point.setChecked(point is not None)
        if point:
            self.point_magnitude.setValue(point.magnitude / 1000)
            self.point_position.setValue(point.position)
        self.use_udl.setChecked(udl is not None)
        if udl:
            self.udl_magnitude.setValue(udl.magnitude / 1000)
        if case.criterion.custom_allowable is not None:
            self.criterion.setCurrentIndex(self.criterion.findData("custom"))
            self.custom_allowable.setValue(case.criterion.custom_allowable * 1000)
        else:
            self.criterion.setCurrentIndex(self.criterion.findData(float(case.criterion.ratio)))

    def reset_form(self) -> None:
        self.project_name.setText(self._t("example_project"))
        self.calc_title.setText(self._t("example_title"))
        self.engineer.clear()
        self.notes.clear()
        self.beam_type.setCurrentIndex(self.beam_type.findData(BeamType.SIMPLY_SUPPORTED.value))
        self.length_unit.setCurrentText("m")
        self.beam_length.setValue(4.0)
        self.material_preset.setCurrentIndex(self.material_preset.findData("S355"))
        self.section_type.setCurrentIndex(self.section_type.findData("rectangular"))
        self.rect_width.setValue(100)
        self.rect_height.setValue(200)
        self.use_point.setChecked(True)
        self.point_magnitude.setValue(10)
        self.point_position.setValue(2)
        self.use_udl.setChecked(False)
        self.udl_magnitude.setValue(2)
        self.criterion.setCurrentIndex(self.criterion.findData(250.0))
        self.current_result = None
        self.export_button.setEnabled(False)
