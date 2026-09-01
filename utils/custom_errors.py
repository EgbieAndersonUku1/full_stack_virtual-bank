
class TempImageStorageError(Exception):
    pass


class MissingUploadedImageFile(Exception):
    pass



class LargeFileImageError(Exception):
    pass


class UnsupportedFormatError(Exception):
    pass


class IncorrectImageDimensionError(Exception):
    pass


class PredifinedBanksCreationError(Exception):
    pass


class MissingBankInformationError(Exception):
    pass


class OnBoardingFailureError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


class IncorrectAddressPartTypeError(Exception):
    pass


class CardRequestApplicationTypeError(Exception):
    pass


class BankAccountTypeError(Exception):
    pass


class IncorrectAmountError(Exception):
    pass


class IncorrectAmountTypeError(Exception):
    pass


class MissingCurrentAccountError(Exception):
    pass


class MissingAccountError(Exception):
    pass


class DateTimeError(Exception):
    pass
