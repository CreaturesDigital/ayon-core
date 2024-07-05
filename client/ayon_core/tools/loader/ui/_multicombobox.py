from qtpy import QtWidgets, QtCore, QtGui

from ayon_core.tools.utils.lib import (
    checkstate_int_to_enum,
    checkstate_enum_to_int,
)
from ayon_core.tools.utils.constants import (
    CHECKED_INT,
    UNCHECKED_INT,
    ITEM_IS_USER_TRISTATE,
)


class CustomPaintDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate showing status name and short name."""
    _checked_value = checkstate_enum_to_int(QtCore.Qt.Checked)
    _checked_bg_color = QtGui.QColor("#2C3B4C")

    def __init__(
        self,
        text_role,
        short_text_role,
        text_color_role,
        icon_role,
        parent=None
    ):
        super().__init__(parent)
        self._text_role = text_role
        self._text_color_role = text_color_role
        self._short_text_role = short_text_role
        self._icon_role = icon_role

    def paint(self, painter, option, index):
        if option.widget:
            style = option.widget.style()
        else:
            style = QtWidgets.QApplication.style()

        self.initStyleOption(option, index)

        mode = QtGui.QIcon.Normal
        if not (option.state & QtWidgets.QStyle.State_Enabled):
            mode = QtGui.QIcon.Disabled
        elif option.state & QtWidgets.QStyle.State_Selected:
            mode = QtGui.QIcon.Selected
        state = QtGui.QIcon.Off
        if option.state & QtWidgets.QStyle.State_Open:
            state = QtGui.QIcon.On
        icon = self._get_index_icon(index)
        option.features |= QtWidgets.QStyleOptionViewItem.HasDecoration

        # Disable visible check indicator
        # - checkstate is displayed by background color
        option.features &= (
            ~QtWidgets.QStyleOptionViewItem.HasCheckIndicator
        )

        option.icon = icon
        act_size = icon.actualSize(option.decorationSize, mode, state)
        option.decorationSize = QtCore.QSize(
            min(option.decorationSize.width(), act_size.width()),
            min(option.decorationSize.height(), act_size.height())
        )

        text = self._get_index_name(index)
        if text:
            option.features |= QtWidgets.QStyleOptionViewItem.HasDisplay
            option.text = text

        painter.save()
        painter.setClipRect(option.rect)

        is_checked = (
            index.data(QtCore.Qt.CheckStateRole) == self._checked_value
        )
        if is_checked:
            painter.fillRect(option.rect, self._checked_bg_color)

        icon_rect = style.subElementRect(
            QtWidgets.QCommonStyle.SE_ItemViewItemDecoration,
            option,
            option.widget
        )
        text_rect = style.subElementRect(
            QtWidgets.QCommonStyle.SE_ItemViewItemText,
            option,
            option.widget
        )

        # Draw background
        style.drawPrimitive(
            QtWidgets.QCommonStyle.PE_PanelItemViewItem,
            option,
            painter,
            option.widget
        )

        # Draw icon
        option.icon.paint(
            painter,
            icon_rect,
            option.decorationAlignment,
            mode,
            state
        )
        fm = QtGui.QFontMetrics(option.font)
        if text_rect.width() < fm.width(text):
            text = self._get_index_short_name(index)
            if not text or text_rect.width() < fm.width(text):
                text = ""

        fg_color = self._get_index_text_color(index)
        pen = painter.pen()
        pen.setColor(fg_color)
        painter.setPen(pen)

        painter.drawText(
            text_rect,
            option.displayAlignment,
            text
        )

        if option.state & QtWidgets.QStyle.State_HasFocus:
            focus_opt = QtWidgets.QStyleOptionFocusRect()
            focus_opt.state = option.state
            focus_opt.direction = option.direction
            focus_opt.rect = option.rect
            focus_opt.fontMetrics = option.fontMetrics
            focus_opt.palette = option.palette

            focus_opt.rect = style.subElementRect(
                QtWidgets.QCommonStyle.SE_ItemViewItemFocusRect,
                option,
                option.widget
            )
            focus_opt.state |= (
                QtWidgets.QStyle.State_KeyboardFocusChange
                | QtWidgets.QStyle.State_Item
            )
            focus_opt.backgroundColor = option.palette.color(
                (
                    QtGui.QPalette.Normal
                    if option.state & QtWidgets.QStyle.State_Enabled
                    else QtGui.QPalette.Disabled
                ),
                (
                    QtGui.QPalette.Highlight
                    if option.state & QtWidgets.QStyle.State_Selected
                    else QtGui.QPalette.Window
                )
            )
            style.drawPrimitive(
                QtWidgets.QCommonStyle.PE_FrameFocusRect,
                focus_opt,
                painter,
                option.widget
            )

        painter.restore()

    def _get_index_name(self, index):
        return index.data(self._text_role)

    def _get_index_short_name(self, index):
        if self._short_text_role is None:
            return None
        return index.data(self._short_text_role)

    def _get_index_text_color(self, index):
        color = None
        if self._text_color_role is not None:
            color = index.data(self._text_color_role)
        if color is not None:
            return QtGui.QColor(color)
        return QtGui.QColor(QtCore.Qt.white)

    def _get_index_icon(self, index):
        icon = None
        if self._icon_role is not None:
            icon = index.data(self._icon_role)
        if icon is None:
            return QtGui.QIcon()
        return icon


# class CustomPaintMultiselectComboBox(QtWidgets.QComboBox):
#     def paintEvent(self, event):
#         painter = QtWidgets.QStylePainter(self)
#         option = QtWidgets.QStyleOptionComboBox()
#         self.initStyleOption(option)
#         painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, option)
#         idx = self.currentIndex()
#         status_name = self.itemData(idx, self._name_role)
#         if status_name is None:
#             painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, option)
#             return
#
#         painter.save()
#
#         status_icon = self.itemData(idx, self._icon_role)
#         content_field_rect = self.style().subControlRect(
#             QtWidgets.QStyle.CC_ComboBox,
#             option,
#             QtWidgets.QStyle.SC_ComboBoxEditField
#         ).adjusted(1, 0, -1, 0)
#
#         metrics = option.fontMetrics
#         version_text_width = metrics.width(option.currentText) + 2
#         version_text_rect = QtCore.QRect(content_field_rect)
#         version_text_rect.setWidth(version_text_width)
#
#         painter.drawText(
#             version_text_rect,
#             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
#             option.currentText
#         )
#
#         status_text_rect = QtCore.QRect(content_field_rect)
#         status_text_rect.setLeft(version_text_rect.right() + 2)
#         if status_icon is not None and not status_icon.isNull():
#             icon_rect = QtCore.QRect(status_text_rect)
#             diff = icon_rect.height() - metrics.height()
#             if diff < 0:
#                 diff = 0
#             top_offset = diff // 2
#             bottom_offset = diff - top_offset
#             icon_rect.adjust(0, top_offset, 0, -bottom_offset)
#             icon_rect.setWidth(metrics.height())
#             status_icon.paint(
#                 painter,
#                 icon_rect,
#                 QtCore.Qt.AlignCenter,
#                 QtGui.QIcon.Normal,
#                 QtGui.QIcon.On
#             )
#             status_text_rect.setLeft(icon_rect.right() + 2)
#
#         if status_text_rect.width() <= 0:
#             return
#
#         if status_text_rect.width() < metrics.width(status_name):
#             status_name = self.itemData(idx, self._short_name_role)
#             if status_text_rect.width() < metrics.width(status_name):
#                 status_name = ""
#
#         color = QtGui.QColor(self.itemData(idx, self._text_color_role))
#
#         pen = painter.pen()
#         pen.setColor(color)
#         painter.setPen(pen)
#         painter.drawText(
#             status_text_rect,
#             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
#             status_name
#         )
#         painter.restore()
#         painter.end()


class CustomPaintMultiselectComboBox(QtWidgets.QComboBox):
    value_changed = QtCore.Signal()
    focused_in = QtCore.Signal()

    ignored_keys = {
        QtCore.Qt.Key_Up,
        QtCore.Qt.Key_Down,
        QtCore.Qt.Key_PageDown,
        QtCore.Qt.Key_PageUp,
        QtCore.Qt.Key_Home,
        QtCore.Qt.Key_End,
    }

    def __init__(
        self,
        name_role,
        short_name_role,
        text_color_role,
        icon_role,
        value_role=None,
        model=None,
        placeholder=None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        if model is not None:
            self.setModel(model)

        combo_view = QtWidgets.QListView(self)

        self.setView(combo_view)

        item_delegate = CustomPaintDelegate(
            name_role,
            short_name_role,
            text_color_role,
            icon_role,
        )
        combo_view.setItemDelegateForColumn(0, item_delegate)

        if value_role is None:
            value_role = name_role

        self._combo_view = combo_view
        self._item_delegate = item_delegate
        self._value_role = value_role
        self._name_role = name_role
        self._short_name_role = short_name_role
        self._text_color_role = text_color_role
        self._icon_role = icon_role

        self._popup_is_shown = False
        self._block_mouse_release_timer = QtCore.QTimer(self, singleShot=True)
        self._initial_mouse_pos = None
        self._placeholder_text = placeholder

        self._custom_text = None

    def get_placeholder_text(self):
        return self._placeholder_text

    def set_placeholder_text(self, text):
        self._placeholder_text = text
        self.repaint()

    def set_custom_text(self, text):
        self._custom_text = text
        self.repaint()

    def focusInEvent(self, event):
        self.focused_in.emit()
        return super().focusInEvent(event)

    def mousePressEvent(self, event):
        """Reimplemented."""
        self._popup_is_shown = False
        super().mousePressEvent(event)
        if self._popup_is_shown:
            self._initial_mouse_pos = self.mapToGlobal(event.pos())
            self._block_mouse_release_timer.start(
                QtWidgets.QApplication.doubleClickInterval()
            )

    def showPopup(self):
        """Reimplemented."""
        super().showPopup()
        view = self.view()
        view.installEventFilter(self)
        view.viewport().installEventFilter(self)
        self._popup_is_shown = True

    def hidePopup(self):
        """Reimplemented."""
        self.view().removeEventFilter(self)
        self.view().viewport().removeEventFilter(self)
        self._popup_is_shown = False
        self._initial_mouse_pos = None
        super().hidePopup()
        self.view().clearFocus()

    def _event_popup_shown(self, obj, event):
        if not self._popup_is_shown:
            return

        current_index = self.view().currentIndex()
        model = self.model()

        if event.type() == QtCore.QEvent.MouseMove:
            if (
                self.view().isVisible()
                and self._initial_mouse_pos is not None
                and self._block_mouse_release_timer.isActive()
            ):
                diff = obj.mapToGlobal(event.pos()) - self._initial_mouse_pos
                if diff.manhattanLength() > 9:
                    self._block_mouse_release_timer.stop()
            return

        index_flags = current_index.flags()
        state = checkstate_int_to_enum(
            current_index.data(QtCore.Qt.CheckStateRole)
        )
        new_state = None

        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if (
                self._block_mouse_release_timer.isActive()
                or not current_index.isValid()
                or not self.view().isVisible()
                or not self.view().rect().contains(event.pos())
                or not index_flags & QtCore.Qt.ItemIsSelectable
                or not index_flags & QtCore.Qt.ItemIsEnabled
                or not index_flags & QtCore.Qt.ItemIsUserCheckable
            ):
                return

            if state == QtCore.Qt.Checked:
                new_state = UNCHECKED_INT
            else:
                new_state = CHECKED_INT

        elif event.type() == QtCore.QEvent.KeyPress:
            # TODO: handle QtCore.Qt.Key_Enter, Key_Return?
            if event.key() == QtCore.Qt.Key_Space:
                if (
                    index_flags & QtCore.Qt.ItemIsUserCheckable
                    and index_flags & ITEM_IS_USER_TRISTATE
                ):
                    new_state = (checkstate_enum_to_int(state) + 1) % 3

                elif index_flags & QtCore.Qt.ItemIsUserCheckable:
                    # toggle the current items check state
                    if state != QtCore.Qt.Checked:
                        new_state = CHECKED_INT
                    else:
                        new_state = UNCHECKED_INT

        if new_state is not None:
            model.setData(current_index, new_state, QtCore.Qt.CheckStateRole)
            self.view().update(current_index)
            self.repaint()
            self.value_changed.emit()
            return True

    def eventFilter(self, obj, event):
        """Reimplemented."""
        result = self._event_popup_shown(obj, event)
        if result is not None:
            return result

        return super().eventFilter(obj, event)

    def addItem(self, *args, **kwargs):
        idx = self.count()
        super().addItem(*args, **kwargs)
        self.model().item(idx).setCheckable(True)

    def paintEvent(self, event):
        """Reimplemented."""
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(option)
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, option)

        idxs = self._get_checked_idx()
        # draw the icon and text
        draw_text = True
        combotext = None
        if self._custom_text is not None:
            combotext = self._custom_text
        elif not idxs:
            combotext = self._placeholder_text
        else:
            draw_text = False

        content_field_rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_ComboBox,
            option,
            QtWidgets.QStyle.SC_ComboBoxEditField
        ).adjusted(1, 0, -1, 0)

        if draw_text:
            color = option.palette.color(QtGui.QPalette.Text)
            color.setAlpha(67)
            pen = painter.pen()
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawText(
                content_field_rect,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                combotext
            )
        else:
            self._paint_items(painter, idxs, content_field_rect)

        painter.end()

    def _paint_items(self, painter, indexes, content_rect):
        origin_rect = QtCore.QRect(content_rect)

        metrics = self.fontMetrics()
        model = self.model()
        available_width = content_rect.width()
        total_used_width = 0

        painter.save()

        spacing = 2

        for idx in indexes:
            index = model.index(idx, 0)
            if not index.isValid():
                continue

            icon = index.data(self._icon_role)
            # TODO handle this case
            if icon.isNull():
                continue

            icon_rect = QtCore.QRect(content_rect)
            diff = icon_rect.height() - metrics.height()
            if diff < 0:
                diff = 0
            top_offset = diff // 2
            bottom_offset = diff - top_offset
            icon_rect.adjust(0, top_offset, 0, -bottom_offset)
            icon_rect.setWidth(metrics.height())
            icon.paint(
                painter,
                icon_rect,
                QtCore.Qt.AlignCenter,
                QtGui.QIcon.Normal,
                QtGui.QIcon.On
            )
            content_rect.setLeft(icon_rect.right() + spacing)
            if total_used_width > 0:
                total_used_width += spacing
            total_used_width += icon_rect.width()
            if total_used_width > available_width:
                break

        painter.restore()

        if total_used_width > available_width:
            ellide_dots = chr(0x2026)
            painter.drawText(origin_rect, QtCore.Qt.AlignRight, ellide_dots)

    def setItemCheckState(self, index, state):
        self.setItemData(index, state, QtCore.Qt.CheckStateRole)

    def set_value(self, values, role=None):
        if role is None:
            role = self._value_role

        for idx in range(self.count()):
            value = self.itemData(idx, role=role)
            if value in values:
                check_state = CHECKED_INT
            else:
                check_state = UNCHECKED_INT
            self.setItemData(idx, check_state, QtCore.Qt.CheckStateRole)
        self.repaint()

    def get_value(self, role=None):
        if role is None:
            role = self._value_role
        items = []
        for idx in range(self.count()):
            state = checkstate_int_to_enum(
                self.itemData(idx, role=QtCore.Qt.CheckStateRole)
            )
            if state == QtCore.Qt.Checked:
                items.append(self.itemData(idx, role=role))
        return items

    def get_all_value_info(self, role=None):
        if role is None:
            role = self._value_role
        items = []
        for idx in range(self.count()):
            state = checkstate_int_to_enum(
                self.itemData(idx, role=QtCore.Qt.CheckStateRole)
            )
            items.append(
                (
                    self.itemData(idx, role=role),
                    state == QtCore.Qt.Checked
                )
            )
        return items

    def _get_checked_idx(self):
        indexes = []
        for idx in range(self.count()):
            state = checkstate_int_to_enum(
                self.itemData(idx, role=QtCore.Qt.CheckStateRole)
            )
            if state == QtCore.Qt.Checked:
                indexes.append(idx)
        return indexes

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        if (
            event.key() == QtCore.Qt.Key_Down
            and event.modifiers() & QtCore.Qt.AltModifier
        ):
            return self.showPopup()

        if event.key() in self.ignored_keys:
            return event.ignore()

        return super().keyPressEvent(event)