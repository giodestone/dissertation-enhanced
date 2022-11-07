import hashlib
from io import BufferedReader, BufferedWriter, TextIOWrapper
import os
import pickle

class ObjectCacher:
    """Caches objects to a directory and provides easy way to load it. 
    """
    OBJECT_CACHER_DEFAULT_FILE_EXTENSION = ".pickle"

    def __init__(self, dir_name:str, file_name:str, description="object"):
        """Create an `ObjectCacher`.
        Args:
            dir_name (str): Name of the directory which the items should be cached to. Should be unique.
            file_name (str): Name of the file. For saving & loading to cache correctly, it must be the same across program launches.
            description (str, optional): A description of what is being saved. Defaults to "object".
        """
        self.__dir_name = dir_name
        self.__file_name = file_name
        self.__description = description


    def is_saved_on_disk(self) -> bool:
        """Whether the file is cached."""
        return os.path.exists(self.__get_file_path_to_cached_obj())


    def load_from_disk(self) -> any:
        """Load the file from disk, if cached.

        Returns:
            any: The pickled object, `None` if not found.
        """
        print("Loading {desc} from disk...".format(desc=self.__description))
        
        if not self.is_saved_on_disk():
            print ("Not found on disk.")
            return None

        with open(self.__get_file_path_to_cached_obj(), 'rb') as f:
            obj = self._on_load(f)

        print("Loaded!")
        return obj


    def _on_load(self, f:BufferedReader) -> any:
        """Returns the file loaded on the disk. This function may be extended.

        Returns:
            any: File located at the object.
        """
        return pickle.load(f)


    def save_to_disk(self, obj_to_save:any) -> None:
        """Save the file to disk.
        """
        print("Saving {desc} to disk...".format(desc=self.__description))

        if not os.path.exists(self.__dir_name + "/"):
            os.mkdir(self.__dir_name)

        with open(self.__get_file_path_to_cached_obj(), 'wb') as f:
            self._on_save(obj_to_save, f)

        print("Saved!")
        pass


    def _on_save(self, obj_to_save:any, f:BufferedWriter):
        """Saves the object to disk. Can be extended.
        """
        pickle.dump(obj_to_save, f)


    def __get_file_path_to_cached_obj(self) -> str:
        """Get the hypothetical file path to the cached object. May not exist on disk.
        """
        hash_object = hashlib.sha256(self.__file_name.encode("utf-8"))
        hex_dig_of_name = hash_object.hexdigest()
        return self.__dir_name + "/" + hex_dig_of_name + self.OBJECT_CACHER_DEFAULT_FILE_EXTENSION
