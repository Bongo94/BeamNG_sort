# mod_analyzer.py
import zipfile
import json
import os
from typing import Optional, List, Dict
from core.mod_info import ModInfo, ModType  # Импорт из mod_info.py
from utils.logger import logger  # Импортируем логгер

class ModAnalyzer:
    @staticmethod
    def analyze_zip(zip_path: str) -> ModInfo:
        logger.debug(f"Analyzing zip file: {zip_path}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = zf.namelist()
                logger.debug(f"File list: {file_list}")

                vehicle_info = ModAnalyzer._check_vehicle_mod(zf, file_list)
                if vehicle_info:
                    logger.info(f"Detected vehicle mod: {vehicle_info.name}")
                    return vehicle_info

                map_info = ModAnalyzer._check_map_mod(zf, file_list)
                if map_info:
                    logger.info(f"Detected map mod: {map_info.name}")
                    return map_info

                other_info = ModAnalyzer._create_other_mod_info(zf, file_list)
                logger.info(f"Detected other mod: {other_info.name}")
                return other_info
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid zip file: {zip_path} - {e}")
            return ModAnalyzer._create_fallback_mod_info(zipfile.ZipFile(zip_path, 'r'), "", ModType.OTHER, f"Invalid zip file: {e}")
        except Exception as e:
            logger.exception(f"Error analyzing zip file: {zip_path}")
            # If the zip file is corrupted, we can't even get the file list, so pass an empty string as a fallback.
            return ModAnalyzer._create_fallback_mod_info(zipfile.ZipFile(zip_path, 'r'), "", ModType.OTHER, str(e))

    @staticmethod
    def _check_vehicle_mod(zf: zipfile.ZipFile, file_list: List[str]) -> Optional[ModInfo]:
        logger.debug(f"Checking for vehicle mod in {zf.filename}")
        info_file = next((name for name in file_list
                          if 'vehicles' in name.split('/') and 'info.json' in name), None)

        if not info_file:
            logger.debug("No vehicle info.json found.")
            return None

        logger.debug(f"Found vehicle info.json: {info_file}")
        try:
            with zf.open(info_file) as f:
                info = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"JSONDecodeError in _check_vehicle_mod: {e}")
            return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.VEHICLE, str(e))
        except Exception as e:
            logger.exception(f"Error in _check_vehicle_mod")
            return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.VEHICLE, str(e))

        logger.debug(f"Vehicle info: {info}")

        # Get all preview images and configurations
        preview_images = []
        base_dir = os.path.dirname(info_file)
        logger.debug(f"Base directory: {base_dir}")

        # Find all .pc files and corresponding images
        pc_files = [f for f in file_list if f.startswith(base_dir) and f.endswith('.pc')]
        logger.debug(f"PC files: {pc_files}")

        for pc_file in pc_files:
            config_name = os.path.splitext(os.path.basename(pc_file))[0]
            # Look for matching image
            img_base = os.path.join(base_dir, config_name).replace('\\', '/')  # Normalize path to forward slashes
            logger.debug(f"Image base: {img_base}")
            for ext in ['.png', '.jpg', '.jpeg']:
                img_path = img_base + ext
                if img_path in file_list:
                    try:
                        with zf.open(img_path) as img:
                            data = img.read()
                            logger.debug(f"Found image {img_path} with {len(data)} bytes")
                            preview_images.append((config_name, data))
                            break  # Found the image, skip other extensions
                    except Exception as e:
                        logger.warning(f"Could not load image {img_path}: {e}")


        # Add default image if exists
        for default_name in ['default.png', 'default.jpg']:
            default_path = os.path.join(base_dir, default_name).replace('\\', '/')  # Normalize path to forward slashes
            if default_path in file_list:
                try:
                    with zf.open(default_path) as img:
                        data = img.read()
                        logger.debug(f"Found default image {default_path} with {len(data)} bytes")
                        preview_images.insert(0, ('default', data))
                except Exception as e:
                    logger.warning(f"Could not load default image {default_path}: {e}")


        mod_info = ModInfo(
            name=info.get('Name', 'Unknown'),
            author=info.get('Author', 'Unknown'),
            type=ModType.VEHICLE,
            description=ModAnalyzer._format_vehicle_description(info),
            preview_images=preview_images,
            additional_info={
                'country': info.get('Country'),
                'derby_class': info.get('Derby Class'),
                'type': info.get('Type'),
                'paints': info.get('paints', {}),
                'configurations': [os.path.splitext(os.path.basename(pc))[0] for pc in pc_files],
                'raw_info': info
            }
        )
        logger.info(f"Vehicle mod detected: {mod_info.name}")
        return mod_info

    @staticmethod
    def _format_vehicle_description(info: Dict) -> str:
        logger.debug(f"Formatting vehicle description for: {info.get('Name', 'Unknown')}")
        desc_parts = [
            f"Brand: {info.get('Brand', 'N/A')}",
            f"Body Style: {info.get('Body Style', 'N/A')}",
            f"Years: {info.get('Years', {}).get('min', 'N/A')}-{info.get('Years', {}).get('max', 'N/A')}",
            f"Country: {info.get('Country', 'N/A')}",
            f"Derby Class: {info.get('Derby Class', 'N/A')}",
            f"Type: {info.get('Type', 'N/A')}"
        ]

        if 'Engine' in info:
            engine = info['Engine']
            logger.debug(f"Engine details: {engine}")
            desc_parts.extend([
                "\nEngine Details:",
                f"Type: {engine.get('Type', 'N/A')}",
                f"Configuration: {engine.get('Configuration', 'N/A')}",
                f"Displacement: {engine.get('Displacement', 'N/A')}",
                f"Power: {engine.get('Power', 'N/A')}"
            ])

        if 'Transmission' in info:
            trans = info['Transmission']
            logger.debug(f"Transmission details: {trans}")
            desc_parts.extend([
                "\nTransmission:",
                f"Type: {trans.get('Type', 'N/A')}",
                f"Gears: {trans.get('Gears', 'N/A')}"
            ])

        description = "\n".join(desc_parts)
        logger.debug(f"Formatted description: {description}")
        return description

    @staticmethod
    def _check_map_mod(zf: zipfile.ZipFile, file_list: List[str]) -> Optional[ModInfo]:
        """Check if zip contains map mod structure and extract info"""
        logger.debug(f"Checking for map mod in {zf.filename}")
        info_file = next((name for name in file_list
                          if 'levels' in name.split('/') and 'info.json' in name), None)

        if not info_file:
            logger.debug("No map info.json file found.")
            return None

        logger.debug(f"Found map info.json: {info_file}")
        try:
            with zf.open(info_file) as f:
                info = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"JSONDecodeError in _check_map_mod: {e}")
            return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.MAP, str(e))
        except Exception as e:
            logger.exception(f"Error in _check_map_mod")
            return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.MAP, str(e))

        logger.debug(f"Map info: {info}")
        preview_images = []
        base_dir = os.path.dirname(info_file)

        # Get all preview images with their names
        for preview in info.get('previews', []):
            preview_path = os.path.join(base_dir, preview)
            if preview_path in file_list:
                try:
                    with zf.open(preview_path) as img:
                        preview_images.append((os.path.basename(preview), img.read()))
                        logger.debug(f"Found map preview image: {preview_path}")
                except Exception as e:
                    logger.warning(f"Could not load preview image {preview_path}: {e}")

        mod_info = ModInfo(
            name=info.get('title', 'Unknown Map'),
            author=info.get('authors', 'Unknown'),
            type=ModType.MAP,
            description=ModAnalyzer._format_map_description(info),
            preview_images=preview_images,
            additional_info={
                'roads': info.get('roads'),
                'suitable_for': info.get('suitablefor'),
                'spawn_points': info.get('spawnPoints', []),
                'raw_info': info
            }
        )

        logger.info(f"Map mod detected: {mod_info.name}")
        return mod_info

    @staticmethod
    def _format_map_description(info: Dict) -> str:
        logger.debug(f"Formatting map description for: {info.get('title', 'Unknown Map')}")
        desc_parts = [
            f"Biome: {info.get('biome', 'N/A')}",
            f"Size: {' x '.join(map(str, info.get('size', ['N/A', 'N/A'])))}",
            f"\nDescription: {info.get('description', 'N/A')}",
            f"\nRoads: {', '.join(info.get('roads', ['N/A']))}",
            f"Suitable for: {', '.join(info.get('suitablefor', ['N/A']))}"
        ]
        description = "\n".join(desc_parts)
        logger.debug(f"Formatted description: {description}")
        return description

    @staticmethod
    def _create_other_mod_info(zf: zipfile.ZipFile, file_list: List[str]) -> ModInfo:
        logger.debug(f"Creating 'other' mod info for: {zf.filename}")
        info_file = next((name for name in file_list if name.endswith('info.json')), None)
        info = {}

        if info_file:
            logger.debug(f"Found info.json: {info_file}")
            try:
                with zf.open(info_file) as f:
                    info = json.load(f)
                    logger.debug(f"Loaded info.json: {info}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSONDecodeError in _create_other_mod_info: {e}")
                return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.OTHER, str(e))
            except Exception as e:
                logger.exception(f"Error in _create_other_mod_info")
                return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.OTHER, str(e))

        preview_images = []
        image_files = [f for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        logger.debug(f"Image files: {image_files}")
        for img_file in image_files[:3]:
            try:
                with zf.open(img_file) as img:
                    data = img.read()
                    logger.debug(f"Found image {img_file} with {len(data)} bytes")
                    preview_images.append((os.path.basename(img_file), data))
            except Exception as e:
                logger.warning(f"Could not load image {img_file}: {e}")


        mod_info = ModInfo(
            name=info.get('name', info.get('title', os.path.basename(zf.filename))),
            author=info.get('author', info.get('authors', 'Unknown')),
            type=ModType.OTHER,
            description="Unknown mod type. Please review contents manually.",
            preview_images=preview_images,
            additional_info=info
        )

        logger.info(f"Created 'other' mod info: {mod_info.name}")
        return mod_info

    @staticmethod
    def _create_fallback_mod_info(zf: zipfile.ZipFile, info_file_path: str, mod_type: ModType,
                                  error_message: str) -> ModInfo:
        """Creates a ModInfo object when JSON parsing fails."""
        logger.error(f"Creating fallback ModInfo for {zf.filename} due to: {error_message}")

        # Attempt to get a mod name from the filename
        try:
            mod_name = os.path.basename(zf.filename).replace(".zip", "")  # Fallback name
        except:
            mod_name = "Unknown Mod"

        # Try to get at least *some* preview images, even if JSON is broken
        preview_images = []
        base_dir = os.path.dirname(info_file_path) if info_file_path else ""
        file_list = zf.namelist()

        # Look for common image extensions in a couple of likely locations
        for image_ext in ('.png', '.jpg', '.jpeg'):
            # Check in the same directory as the (potentially broken) info file
            if info_file_path:
                potential_image_path = os.path.join(base_dir, "preview" + image_ext).replace('\\', '/')
                if potential_image_path in file_list:
                    try:
                        with zf.open(potential_image_path) as img:
                            preview_images.append((os.path.basename(potential_image_path), img.read()))
                            logger.debug(f"Found fallback image {potential_image_path}")
                            if len(preview_images) >= 3:
                                break  # Limit to 3 previews
                    except Exception as e:
                        logger.warning(f"Could not load fallback image {potential_image_path}: {e}")

            # If we still don't have images, try a more general search within the zip
            if len(preview_images) < 3:
                for file_name in file_list:
                    if file_name.lower().endswith(image_ext):
                        try:
                            with zf.open(file_name) as img:
                                preview_images.append((os.path.basename(file_name), img.read()))
                                logger.debug(f"Found fallback image {file_name}")
                                if len(preview_images) >= 3:
                                    break
                        except Exception as e:
                            logger.warning(f"Could not load fallback image {file_name}: {e}")


        mod_info = ModInfo(
            name=mod_name,
            author="Unknown (JSON Error)",
            type=mod_type,  # Use provided type
            description=f"Error parsing info.json: {error_message}\n\nCould not load mod details.",
            preview_images=preview_images,
            additional_info={}  # No additional info if JSON is broken
        )
        logger.info(f"Created fallback mod info: {mod_info.name}")
        return mod_info