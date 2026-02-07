// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'logbook_entry.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class LogbookEntryAdapter extends TypeAdapter<LogbookEntry> {
  @override
  final typeId = 0;

  @override
  LogbookEntry read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return LogbookEntry(
      uid: fields[0] as String,
      title: fields[1] as String,
      timestamp: fields[2] as DateTime,
      thumbnailBytes: fields[3] as Uint8List,
      imageBytes: fields[4] as Uint8List,
      analysisResultJson: fields[5] as String,
    );
  }

  @override
  void write(BinaryWriter writer, LogbookEntry obj) {
    writer
      ..writeByte(6)
      ..writeByte(0)
      ..write(obj.uid)
      ..writeByte(1)
      ..write(obj.title)
      ..writeByte(2)
      ..write(obj.timestamp)
      ..writeByte(3)
      ..write(obj.thumbnailBytes)
      ..writeByte(4)
      ..write(obj.imageBytes)
      ..writeByte(5)
      ..write(obj.analysisResultJson);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is LogbookEntryAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
